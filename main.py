
import numpy as np
import random
from typing import Callable
from queue import PriorityQueue

from numpy.core.fromnumeric import argmax

class StudentPicker:
    def __init__(self,question_scores,student_answers:dict,question_names:list,profesor_name="Auxiliar"):
        self.questions_scores    = np.array(question_scores)
        self.num_questions       = len(self.questions_scores)
        self.students_questions  = student_answers
        self.students            = student_answers.keys()
        self.question_names      = question_names
        self.profesor_name       = profesor_name
    
    def random_partitioner(self,partitions: int):
        student_list = list(self.students)
        random.shuffle(student_list)

        Partitions = [[] for _i in range(partitions)]
        for i,student in enumerate(student_list):
            p = int(i%partitions)
            Partitions[p].append(student)
        return Partitions
    
    @staticmethod
    def partition_list(student_list:list, partitions: int):
        Partitions = [[] for _i in range(partitions)]
        for i,student in enumerate(student_list):
            p = int(i%partitions)
            Partitions[p].append(student)
        return Partitions
    
    def total_score_queue(self):
        _queue = PriorityQueue(maxsize=len(self.students)+1)
        scores = np.array(self.questions_scores)
        for student,questions in self.students_questions.items():
            solveds = np.array(questions)
            score = np.dot(solveds,scores)
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

    def scored_partitioner(self,partitions: int):
        student_list = self.total_score_sorted_list()
        return student_picker.partition_list(student_list,partitions)
    
    def shuffled_scored_partitioner(self,partitions : int, shufflers_step:int):
        _list = self.total_score_sorted_list()
        # shuffler
        shuffler = []
        for i,student in enumerate(_list):
            # create another shuffler every 'shuffler_step' steps
            if i%shufflers_step==0:
                shuffler.append([])
            shuffler[-1].append(student) # add current student to the shuffler
        
        for sub_list in shuffler:
            random.shuffle(sub_list)

        student_list = [student for sub_list in shuffler for student in sub_list]
        return student_picker.partition_list(student_list,partitions)
    
    def partition_solved_counts(self,partition):
        solved_counts = []
        num_questions = len(self.questions_scores)
        for part_number, part in enumerate(partition):
            question_counts = np.zeros(num_questions)
            for student in part:
                student_solved = np.array(self.students_questions[student])
                question_counts+=student_solved
            solved_counts.append(question_counts)
        return solved_counts
    
    def question_assignment(self,partition,coin_toss_weight:Callable=(lambda x:x**1.5),tries:int=100):
        assignments = []
        solved_counts = self.partition_solved_counts(partition)
        for part_number, part in enumerate(partition):
            part_solved_counts = solved_counts[part_number]
            unsolveds = [i for i,count in enumerate(part_solved_counts) if count<=0 ]
            solveds   = [i for i,count in enumerate(part_solved_counts) if count>0  ]
            part_assignment = {}

            assignment_priority = PriorityQueue(maxsize=self.num_questions+1)
            for i in solveds:
                assignment_priority.put((part_solved_counts[i],i))
            
            student_weight = dict([(student,0.0) for student in part])
            weight_sum     = lambda st_charge : float(sum([c for c in st_charge.values()]))

            while(not assignment_priority.empty()):
                i = assignment_priority.get()[1]
                question_name = self.question_names[i]
                student_candidates = [student for student,questions in self.students_questions.items() if questions[i]>0 and student in part]
                # pick student, with probability decreasing
                # with respect to "charge", the amount of times
                # the student has solved the problem in the board.
                student = None
                weight  = weight_sum(student_weight) 
                # try some candidates at random
                for _try in range(tries):
                    # choose if candidate has not been to the board
                    candidate = random.choice(student_candidates)
                    if float(student_weight[candidate])==0:
                        student=candidate
                        break
                # if that fails, estimate best fit via numerous tries
                if student==None:
                    number_of_candidates = len(student_candidates)
                    coin_counter = np.zeros(number_of_candidates)
                    for _try in range(tries):
                        randint   = random.randint(0,number_of_candidates-1)
                        candidate = student_candidates[randint]
                        candidate_weight = float(student_weight[candidate])
                        relative_weight  = candidate_weight/weight
                        coin_toss = coin_toss_weight(relative_weight)
                        coin_toss_trial = np.random.random()
                        coin_counter[randint]+=1.0*(coin_toss_trial<coin_toss)
                    student_id = np.argmax(coin_counter)
                    student=student_id
                #end
                part_assignment[question_name] = student if student!=None else self.profesor_name 
                if student!=None:
                    student_weight[student]+=1
            # assign unsolveds
            for i in unsolveds:
                name = self.question_names[i]
                part_assignment[name] = self.profesor_name
            assignments.append(part_assignment)
            _tuple = (partition,assignments)
        return _tuple
    

    def unsolved_from_partition(self,partition):
        counts = self.partition_solved_counts(partition)
        bad_partitions = []
        for part_number,part in enumerate(partition):
            questions_solveds = counts[part_number]
            if not all(questions_solveds):
                not_solveds = [i for i in range(self.num_questions) if not questions_solveds[i]]
                not_solved_names = [self.question_names[i] for i in not_solveds]
                bad_partitions.append({
                    "part number"       : part_number,
                    "part"              : part,
                    "not solveds"       : not_solveds,
                    "not solveds names" : not_solved_names,
                    "solved counts"     : questions_solveds,
                })
        return bad_partitions
    
    def partition_report(self,partition):
        print("----  Partition Report  ----")
        bad_partitions = self.unsolved_from_partition(partition)
        if len(bad_partitions)!=0:
            print("There are partitions with unsolved questions!")
            print("Note: in this case, unsolved questions are assigned to {profesor} by default.".format(profesor=self.profesor_name))
            for each in bad_partitions:
                print("part number          : ",each["part number"])
                print("part                 : ",each["part"])
                print("unsolved questions   : ",each["not solveds names"])
        else:
            print("Every partition solved all of its questions!")
        print()
        
    def question_count_report(self):
        print("---- Question Report ----")
        question_counts = np.zeros(self.num_questions)
        for _student,solved in self.students_questions.items():
            student_solved  =  np.array(solved)
            question_counts += student_solved
        
        # sort counts
        sorted_count = [(count,self.question_names[question]) for question,count in enumerate(question_counts)]
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

    def assignments_report(self,assignment_tuple):
        print("---- Problem Assignation ----")
        partition   = assignment_tuple[0]
        assign_list = assignment_tuple[1]
        for group,assign in enumerate(assign_list):
            students = partition[group]
            print("For the students in group {:>2}".format(group))
            print(students)
            print("The problems are:")
            for question_name in self.question_names:
                person = assign[question_name]
                print("{:<4} : {:>20}".format(question_name,person))
            print()
        print()
    
    def grade(self,student):
        scores    = self.questions_scores
        maximum_attainable_score = np.sum(scores)
        questions = np.array(self.students_questions[student])
        student_scores = np.dot(questions,scores)
        grade = 1 + 6.0*(student_scores/maximum_attainable_score)
        return grade

if __name__=="__main__":
    np.random.seed() # randomness

    questions_scores = [1,2,2,1,1]
    questions_names  = ["P1a","P1b","P2","P3a","P3b"]
    # p1a : 1
    # p1b : 2
    # p2  : 2
    # p3a : 2
    # p3b : 1

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

    picker     = StudentPicker(questions_scores,students_answers,questions_names)

    groups    = 2
    shufflers = 3 #sub arrays

    partition  = picker.shuffled_scored_partitioner(2,3)
    assignment = picker.question_assignment(partition)

    picker.question_count_report()
    picker.partition_report(partition)
    picker.assignments_report(assignment)


