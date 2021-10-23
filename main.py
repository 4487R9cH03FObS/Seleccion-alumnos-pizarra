# Author: Francisco Aliaga

import numpy as np
import random
from typing import Callable
from queue import PriorityQueue

class StudentPicker:
    # constructor
    # problem set scores: a list/array with the score of each problem.
    # problem set names : a list with the name of each problem, in corresponding order to the problem set scores list.
    # student answers   : a dictionary mapping student -> array consisting of solved problems, with 1 indicating solved and 0 if not. (hot encoding)
    # profesor name     : for handling assignment on problems that not a single student solved.
    def __init__(self,problem_set_scores,problem_set_names:list,student_answers:dict,profesor_name="Auxiliar"):
        self.problem_set_scores    = np.array(problem_set_scores)
        self.num_questions         = len(self.problem_set_scores)
        self.students_answers      = student_answers
        self.students              = student_answers.keys()
        self.problem_set_names     = problem_set_names
        self.profesor_name         = profesor_name
    
    ## main methods

    # partition list:
    # given a student list and a number of partitions,
    # it generates a partition consisting of several balanced lists.
    # the partition depends on the order of the list.
    @staticmethod
    def partition_list(student_list:list, partitions: int):
        Partitions = [[] for _i in range(partitions)]
        for i,student in enumerate(student_list):
            p = int(i%partitions)
            Partitions[p].append(student)
        return Partitions

    # shuffle_scored_partitioner:
    # given an amount of partitions and a size of a "shuffler"
    # generates a partition with balanced student scores.
    # the best students always go to separate groups.
    def shuffled_scored_partitioner(self,partitions : int, shuffler_sizes:int):
        _list = self.total_score_sorted_list()
        # shuffler
        shuffler = []
        for i,student in enumerate(_list):
            # create another shuffler every 'shuffler_sizes' steps
            if i%shuffler_sizes==0:
                shuffler.append([])
            shuffler[-1].append(student) # add current student to the shuffler
        
        for sub_list in shuffler:
            random.shuffle(sub_list)

        student_list = [student for sub_list in shuffler for student in sub_list]
        return StudentPicker.partition_list(student_list,partitions)

    # question_assignemnts:
    # given a partition of students, a "coin_toss_weight formula" and an amount of randomized trials,
    # generates assignment of students to problems they have solved, for each group of student in the partition.
    # the probability of selecting a student decreases everytime the student is selected for a problem, weighted by the difficulty of those problems.
    def question_assignment(self,partition,coin_toss_weight:Callable=(lambda x:x**1.5),tries:int=100):
        # this list will have the problem assignment for each part of the partition
        assignments = []
        # problem solve counts, listing how many times each question was solved
        problem_solve_counts = self.partition_solved_counts(partition)
        for part_number, part in enumerate(partition):
            # contains question assignment for this part
            part_assignment = {}
            # problem solve counts, listing how many times each question was solved
            part_problem_solve_counts = problem_solve_counts[part_number]

            # list of unsolved problems
            unsolved_problems = [i for i,count in enumerate(part_problem_solve_counts) if count<=0 ]
            # list of solved problems, starting by the least solved problem.
            # (first we will assign the problems which are harder to assign).
            solved_problems   = [(count,i) for i,count in enumerate(part_problem_solve_counts) if count>0  ]
            solved_problems.sort()
            
            # student weight summarizes amount of problems to solve at the board.
            # (the amount of times  the student has solved a problem in the board, multiplied by the score of those prroblems)
            # starts at 0
            student_weight = dict([(student,0.0) for student in part])
            weight_sum     = lambda student_weight_ : float(sum([c for c in student_weight_.values()]))

            for ith_problem in solved_problems:
                i             = ith_problem[1]
                question_name = self.problem_set_names[i]

                # list of students in this partition who solved the ith-problem
                student_candidates = [student for student,st_questions in self.students_answers.items() if st_questions[i]>0 and student in part]
                student = None

                ## main idea here:
                # chose a student with probability decreasing
                # with respect to "student weight" 
                # 2 steps:
                # 1. try uniform selection among candidates with zero weight.
                # 2. if that set is almost surely empty, randomize based on weighted coin tosses

                # 1.
                # choose a candidate, if not been to the board, pick.
                # try various times. 
                for _try in range(tries):
                    candidate = random.choice(student_candidates)
                    if float(student_weight[candidate])==0:
                        student=candidate 
                        break
                # 2.
                if student==None:
                    number_of_candidates = len(student_candidates)
                    weight               = weight_sum(student_weight) 
                    coin_counter         = np.zeros(number_of_candidates)
                    ## main idea:
                    # pick a candidate at random, let flip a coin and repeat the tries several times
                    # the one with most coins landing tails, gets to the board.
                    # note: the picked candidate coin has more probability of landing tails
                    # if he has made less problems/less hard problems
                    for _try in range(tries):
                        # pick a candidate at random
                        randint          = random.randint(0,number_of_candidates-1)
                        candidate        = student_candidates[randint]
                        # weight of the coin is determined by its share of solved problems among total
                        candidate_weight = float(student_weight[candidate])
                        relative_weight  = candidate_weight/weight
                        # the coin has weight, and is flipped using random(0,1)
                        _coin_toss_weight  = coin_toss_weight(relative_weight) # e.g. 0 probability of tails if candidate_weight=0
                        coin_toss_trial    = np.random.random()
                        tails              = (coin_toss_trial<_coin_toss_weight) # coin = tails with probability _coin_toss_weight
                        # update number of tails the candidate has flipped
                        coin_counter[randint] += 1.0*tails
                    # choose the one that has flipped most tails
                    student_id = np.argmax(coin_counter)
                    student=student_id
                #end
                ##  assign selected student to problem.
                part_assignment[question_name] = student if student!=None else self.profesor_name 
                # add weight proportional to question difficulty (based on score)
                question_weight = problem_set_scores[self.problem_set_names.index(question_name)]
                if student!=None:
                    student_weight[student]+=question_weight
            # For the unsolved questions,
            # they are assigned to the profesor by default.
            for i in unsolved_problems:
                name = self.problem_set_names[i]
                part_assignment[name] = self.profesor_name
            assignments.append(part_assignment)
        # return
        partition_assignment_tuple = (partition,assignments)
        cleaned_result = self.clean_partition_assignment_tuple(partition_assignment_tuple)
        return cleaned_result
    
    ## useful stuff and experiments

    def clean_partition_assignment_tuple(self,partition_assignment_tuple):
        partition   = partition_assignment_tuple[0]
        assign_list = partition_assignment_tuple[1]
        result = [(group,partition[group],[(question_name,assign[question_name]) for question_name in self.problem_set_names]) for group,assign in enumerate(assign_list)]
        return result

    def scored_partitioner(self,partitions: int):
        student_list = self.total_score_sorted_list()
        return StudentPicker.partition_list(student_list,partitions)
    
    def random_partitioner(self,partitions: int):
        student_list = list(self.students)
        random.shuffle(student_list)

        Partitions = [[] for _i in range(partitions)]
        for i,student in enumerate(student_list):
            p = int(i%partitions)
            Partitions[p].append(student)
        return Partitions
    
    def total_score_queue(self):
        _queue = PriorityQueue(maxsize=len(self.students)+1)
        scores = np.array(self.problem_set_scores)
        for student,questions in self.students_answers.items():
            solved_problems = np.array(questions)
            score = np.dot(solved_problems,scores)
            _queue.put((-score,student))
        return _queue
    
    def total_score_sorted_list(self):
        _queue = self.total_score_queue()
        _list = []
        while not _queue.empty():
            _list.append(_queue.get()[1])
        return _list

    def total_score_list(self):
        _queue = self.total_score_queue()
        _list = []
        while not _queue.empty():
            obj = _queue.get()
            _list.append((obj[1],-obj[0]))
        return _list
    
    ## to extract valuable information of partitions and assignments

    def partition_solved_counts(self,partition):
        problem_solve_counts = []
        num_questions = len(self.problem_set_scores)
        for part_number, part in enumerate(partition):
            question_counts = np.zeros(num_questions)
            for student in part:
                student_solved = np.array(self.students_answers[student])
                question_counts+=student_solved
            problem_solve_counts.append(question_counts)
        return problem_solve_counts

    def unsolved_from_partition(self,partition):
        counts = self.partition_solved_counts(partition)
        bad_partitions = []
        for part_number,part in enumerate(partition):
            questions_solveds = counts[part_number]
            if not all(questions_solveds):
                not_solveds = [i for i in range(self.num_questions) if not questions_solveds[i]]
                not_solved_names = [self.problem_set_names[i] for i in not_solveds]
                bad_partitions.append({
                    "part number"       : part_number,
                    "part"              : part,
                    "not solved_problems"       : not_solveds,
                    "not solved_problems names" : not_solved_names,
                    "solved counts"     : questions_solveds,
                })
        return bad_partitions
    
    # para hacer reportes
    
    def partition_report(self,partition):
        print()
        print("----  Partition Report  ----")
        bad_partitions = self.unsolved_from_partition(partition)
        if len(bad_partitions)!=0:
            print("Warning: There are partitions with unsolved questions!")
            print("Note: in this case, unsolved questions are assigned to {profesor} by default.".format(profesor=self.profesor_name))
            for each in bad_partitions:
                print("part number          : ",each["part number"])
                print("part                 : ",each["part"])
                print("unsolved questions   : ",each["not solved_problems names"])
        else:
            print("Every partition solved all of its questions!")
        print()
        print("-- Grades in each group")
        for g,group in enumerate(partition):
            grade_list   = [self.grade(student) for student in group]
            average      = np.average(grade_list)
            median       = np.median(grade_list)
            standard_dev = np.std(grade_list)
            _max         = np.max(grade_list)
            _min         = np.min(grade_list)
            response = "Group {g:>2} -> mean: {ave:.1f} median: {med:.1f} std: {std:.1f}  |  min,max : {_min:.1f}-{_max:.1f}".format(g=g,ave=average,med=median,std=standard_dev,_min=_min,_max=_max)
            print(response)
        print()
        
    def question_count_report(self):
        print()
        print("---- Question Report ----")
        question_counts = np.zeros(self.num_questions)
        for _student,solved in self.students_answers.items():
            student_solved  =  np.array(solved)
            question_counts += student_solved
        
        # sort counts
        sorted_count = [(count,self.problem_set_names[question]) for question,count in enumerate(question_counts)]
        sorted_count.sort(reverse=True)
        print("-- Question counts")
        for count,name in sorted_count:
            print("{:<5} : {:<3}".format(name,count))
        print()
        
        print("-- Students by score")
        for student, score in self.total_score_list():
            _grade = self.grade(student)
            print("{:<20} : {:<7} grade: {:.1f}".format(student,score,_grade))
        print()

    def assignment_report(self,assignment,vertical=False):
        print()
        print("---- Problem Assignation ----")
        for group_assignment in assignment:
            group                 = group_assignment[0]
            students              = group_assignment[1]
            problem_student_tuples = group_assignment[2]
            print("For the students in group {:>2}:".format(group))
            StudentPicker.print_group_students(students,vertical)
            print("The problems are:")
            for problem,student in problem_student_tuples:
                print("{:<4} : {:>20}".format(problem,student))
            print()
        print()
    
    @staticmethod
    def print_group_students(students:list,vertical=False):
        n = len(students)
        if vertical:
            for i in range(n):
                print(students[i],end="")
                if i<n-1:
                    print(",")
                else:
                    print()
        else:
            for i in range(n):
                if i==0:
                    print("(",end="")
                print(students[i],end="")
                if i<n-1:
                    print(", ",end="")
                else:
                    print(")")
        print()

    
    def grade(self,student):
        scores    = self.problem_set_scores
        maximum_attainable_score = np.sum(scores)
        questions = np.array(self.students_answers[student])
        student_scores = np.dot(questions,scores)
        grade = 1 + 6.0*(student_scores/maximum_attainable_score)
        return grade

###############################    MAIN    ###############################

if __name__=="__main__":
    np.random.seed() # Randomness

    problem_set_scores = [1,2,2,1,1]
    problem_set_names  = ["P1a","P1b","P2","P3a","P3b"]
    # P1a : 1
    # P1b : 2
    # P2  : 2
    # P3a : 1
    # P3b : 1

    students_answers = {               #hot encoding
        "pedro"       :[1,1,1,1,0],
        "juan"        :[0,1,1,1,0], 
        "diego"       :[0,0,1,1,0],
        "jaime"       :[0,0,0,1,0],
        "francisco"   :[1,1,1,1,1],
        "matias"      :[0,1,1,1,0],
        "camila"      :[0,1,1,1,0],
        "alonso"      :[0,1,1,1,0],
        "natacha"     :[1,1,1,1,0],
        "maya"        :[1,1,1,1,0],
    }

    ###### Construct the picker based on data:
    picker     = StudentPicker(problem_set_scores,problem_set_names,students_answers)

    ###### Make solutions to partition and assignment

    ## shuffled_score_partitioner:
    # 1. Sorts students by their total score, (better grades at the top)
    # 2. Shuffles students in groups of "shuffler_size" in the sorted list, so they stay near their place but not exactly.
    # 3. Goes through the shuffled list sending students to group 1,2,... up to group "number_of_groups".

    number_of_groups  = 2
    shuffler_size     = 3  

    partition  = picker.shuffled_scored_partitioner(number_of_groups,shuffler_size)

    ## question_assignment:
    # this one is a bit more tricky to explain. TODO.

    assignment = picker.question_assignment(partition)

    ###### Report printing

    # Reports the number of problem solved counts by the students, and the grades of the students.
    picker.question_count_report()
    # Reports if there are groups with unsolved problems and group grade statistics.
    picker.partition_report(partition)
    # Reports assignment of problems to each group.
    picker.assignment_report(assignment)
    
    

