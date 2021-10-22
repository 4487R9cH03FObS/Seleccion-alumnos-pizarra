
import numpy as np
import random
from typing import Callable
from queue import PriorityQueue

# DATA
## Table 1
# T1: Questions -> Score
## Table 2
# T2: Students -> {0,1}^Questions (hot encoding)


class student_picker:
    def __init__(self,table_1,table_2:dict,question_names:list,profesor_name="Auxiliar"):
        self.questions_scores    = np.array(table_1)
        self.num_questions       = len(self.questions_scores)
        self.students_questions  = table_2
        self.students            = table_2.keys()
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
            # create another shuffler
            if i%shufflers_step==0:
                shuffler.append([])
            shuffler[-1].append(student)
        
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
    
    def question_assignment(self,partition,coin_toss_weight:Callable=(lambda x:x**1.5),tries:int=1000):
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
            
            student_charge = dict([(student,0.0) for student in part])
            charge_sum     = lambda st_charge : float(sum([c for c in st_charge.values()]))

            while(not assignment_priority.empty()):
                i = assignment_priority.get()[1]
                question_name = self.question_names[i]
                student_candidates = [student for student,questions in self.students_questions.items() if questions[i]>0 and student in part]
                # pick student, with probability decreasing
                # with respect to "charge", the amount of times
                # the student has solved the problem in the board.
                student = None
                charge  = charge_sum(student_charge) 
                counter = 0
                while student==None and counter<tries:
                    candidate = random.choice(student_candidates)
                    candidate_charge = float(student_charge[candidate])
                    if candidate_charge==0:
                        student=candidate
                        continue
                    relative_charge  = candidate_charge/charge
                    coin_toss = coin_toss_weight(relative_charge)
                    coin_toss_trial = np.random.random()

                    if coin_toss_trial < coin_toss:
                        student=candidate
                    counter+=1
                # end while.
                part_assignment[question_name] = student if student!=None else self.profesor_name
                if student!=None:
                    student_charge[student]+=1
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
        print("----  partition report  ----")
        bad_partitions = self.unsolved_from_partition(partition)
        if len(bad_partitions)!=0:
            print("There are partitions with unsolved questions!")
            for each in bad_partitions:
                print("part number          : ",each["part number"])
                print("part                 : ",each["part"])
                print("unsolved questions   : ",each["not solveds names"])
        else:
            print("Every partition solved all of its questions!")
        
    def question_count_report(self):
        print("---- question report ----")
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
        
        print("-- Students by score")
        for student, score in self.total_score_list():
            _grade = self.grade(student)
            print("{:<20} : {:<7}, grade: {:.1f}".format(student,score,_grade))

    def report_assignments(self,assignment_tuple):
        print("---- Problem Assignation ----")
        partition   = assignment_tuple[0]
        assign_list = assignment_tuple[1]
        for n,assign in enumerate(assign_list):
            students = partition[n]
            print("For the students in group ",n)
            print(students)
            print("The Problems are:")
            for question_name in self.question_names:
                person = assign[question_name]
                print("{:<4} : {:>20}".format(question_name,person))
            #for quest,person in assign.items():
    
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

    students_questions = {
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

    picker     = student_picker(questions_scores,students_questions,questions_names)
    partition  = picker.shuffled_scored_partitioner(2,2)
    assignment = picker.question_assignment(partition)

    picker.partition_report(partition)
    picker.question_count_report()
    picker.report_assignments(assignment)
    

    



