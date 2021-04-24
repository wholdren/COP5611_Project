# Will Holdren
# COP 5611
# 4/23/21
# Written in Python 3.9

# This program is an implementation of a lottery scheduling system

import sys, argparse, random

def main():
    parser = argparse.ArgumentParser(
        description='simulate a lottery CPU scheduler')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-j', '--jobs', default=10, help='num of jobs', type=int)
    group.add_argument('-f', '--file', help='input file name', type=str)
    parser.add_argument('-s', '--seed', help='random seed', type=int)
    parser.add_argument('-u', '--uniform', action='store_true',
                        help='set all tasks to take the same time to complete')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='print additional info during simulation')
    parser.add_argument('-t', '--trial', action='store_true',
                        help='run a ticket distribution trial on the job list')
    parser.add_argument('-d', '--delta', default=10,
                        help='processor time-slice in ms', type=int)
    parser.add_argument('-r', '--randomstart', action='store_true',
                        help='randomize start times of jobs')
    parser.add_argument('-g', '--generate', action='store_true',
                        help='generate an input test file using jobs and seed')
    args = parser.parse_args()

    if args.generate:
        # Ignores all other input arguments and only takes jobs and seed
        randSeed = 0
        if args.seed is not None:
            randSeed = args.seed
        gen_input(args.jobs, randSeed)
        return 0

    if args.seed is not None:
        print("Setting random seed to", args.seed, end='\n\n')
        random.seed(args.seed)


    # Input format must be followed for all entries or this will break
    # Format: [int: priority] [int: time-to-complete-ms] [int: start-time]

    # Priority - relative ticket distribution of the process, scale 1-21
    # Time to complete - number of milliseconds the process takes to finish
    # Start time - the time at which the job should be added to active list
    jobs = []
    jobCount = 0
    print("===== Jobs list =====")
    if args.file:
        try:
            f = open(args.file)
        except:
            print("Unable to open file")
            return 1
        for line in f:
            jobCount += 1
            job = line.split()
            if(len(job) != 3):
                continue
            job.append(0)
            job[3] = int(job[2])
            job[2] = int(job[1])
            job[1] = int(job[0])
            job[0] = jobCount
            
            if args.uniform:
                job[2] = 500
            jobs.append(job)
            print("Job {:-3d}: ".format(job[0]),
                  "Priority = {:-2d}   ".format(job[1]),
                  "Time to complete = {:-6d}   ".format(job[2]),
                  "Start time = {}".format(job[3]))
        f.close()
    else:
        curStart = 0
        for i in range(args.jobs):
            # Generate the priority
            jobCount += 1
            job = [jobCount, 0, 0, 0]
            temp = random.randint(1, 100)
            if(temp <= 40):
                job[1] = random.randint(1, 5)
            elif(temp <= 70):
                job[1] = random.randint(6, 10)
            elif(temp <= 85):
                job[1] = random.randint(11, 15)
            elif(temp <= 95):
                job[1] = random.randint(16, 20)
            else:
                job[1] = 21
            
            # Generate the time to complete the task
            job[2] = random.randrange(10*job[1], 100*job[1], 1)
            if args.uniform:
                job[2] = 500
            
            # Generate the time to start next task based on current start time
            job[3] = curStart

            jobs.append(job)
            print("Job {:-3d}: ".format(job[0]),
                  "Priority = {:-2d}   ".format(job[1]),
                  "Time to complete = {:-6d}   ".format(job[2]),
                  "Start time = {}".format(job[3]))
            if(args.randomstart):
                curStart += random.randint(10, 200)
    print()

    # If running a probability distribution trial, overwrite random durations
    # and start times
    if args.trial:
        for job in jobs:
            job[2] = 500
            job[3] = 0
    
    numGroups = 2
    activeGroups = [[] for i in range(numGroups)]
    completeJobs = []
    cpuCounter = 0
    timeSlice = args.delta
    ticketsInUse = [0 for i in range(numGroups)]
    ticketCounts = [[] for i in range(numGroups)]
    groupTicketsInUse = 0
    groupTickets = [0 for i in range(numGroups)]
    winRates = [0 for i in range(jobCount)]
    pulls = 0
    while((not args.trial and len(completeJobs) < jobCount)
          or (args.trial and pulls < 100000)):
        i = 0
        while(i < len(jobs)):
            if(cpuCounter >= jobs[i][3]):
                if args.verbose:
                    # Note, jobs will only be added after a time slice has
                    # finished, so this may differ from assigned start time
                    print("Starting job", jobs[i][0], "at time", cpuCounter)
                priority = jobs[i][1]
                group = 0
                if(priority == 21):
                    # Handle a high priority job by assigning a separate group
                    # with a higher amount of overall tickets
                    group = 1
                    
                activeGroups[group].append(jobs[i])
                jobs.remove(jobs[i])
                curIndex = len(activeGroups[group]) - 1
                if(group == 0):
                    # Tickets proportional to priority
                    # For example, priority 4 has 4x as many as priority 1
                    ticketCounts[group].append(100 * priority)
                elif(group == 1):
                    # Equal tickets for all priority 21 jobs in group 1
                    ticketCounts[group].append(1000)
                ticketsInUse[group] += ticketCounts[group][curIndex]
                # Add extra variable to track remaining time to complete
                duration = activeGroups[group][curIndex][2]
                activeGroups[group][curIndex].append(duration)
                if(groupTickets[group] == 0):
                    if(group == 0):
                        groupTickets[group] = 1000
                        groupTicketsInUse += 1000
                    elif(group == 1):
                        groupTickets[group] = 10000
                        groupTicketsInUse += 10000
                    # Can add functionality for more groups if desired
            else:
                i += 1

        # Draw a ticket and perform "work" on the selected job
        if(groupTicketsInUse == 0):
            # Skip 1 cpu cycle
            cpuCounter += 1
            continue
        group = random.randint(1, groupTicketsInUse)
        for j in range(len(ticketCounts)):
            group -= groupTickets[j]
            if(group <= 0):
                group = j
                break
        winner = random.randint(1, ticketsInUse[group])
        for j in range(len(ticketCounts[group])):
            winner -= ticketCounts[group][j]
            if(winner <= 0):
                winner = j
                break
        
        if args.trial:
            jobNum = activeGroups[group][winner][0] - 1
            winRates[jobNum] += 1
            pulls += 1
        else:
            if(activeGroups[group][winner][4] <= timeSlice):
                cpuCounter += activeGroups[group][winner][4]
                activeGroups[group][winner][4] = cpuCounter
                if args.verbose:
                    print("Job", activeGroups[group][winner][0],
                          "won lottery and finished at time", cpuCounter)
                completeJobs.append(activeGroups[group][winner])
                activeGroups[group].remove(activeGroups[group][winner])
                ticketsInUse[group] -= ticketCounts[group][winner]
                ticketCounts[group].remove(ticketCounts[group][winner])
                if(len(activeGroups[group]) == 0):
                    groupTicketsInUse -= groupTickets[group]
                    groupTickets[group] = 0
            else:
                cpuCounter += timeSlice
                activeGroups[group][winner][4] -= timeSlice

    print("\n===== Finished Jobs =====")
    # Print out the completed job info when done
    if args.trial:
        for jobgroup in activeGroups:
            for job in jobgroup:
                print("Job {:-3d} with priority {:-2d}".format(job[0], job[1]),
                      "won the lottery {:-5d} times".format(winRates[job[0]-1]))
    else:
        for job in completeJobs:
            if args.verbose:
                print("Job {:-3d}: priority = {:-2d} ".format(job[0], job[1]),
                      "runtime = {:-4d} ".format(job[2]),
                      "started at", job[3],
                      "with total time {}".format(job[4]-job[3]))
            else:
                print("Job {:-3d}".format(job[0]), "total time", job[4]-job[3])
    return 0


# For use in the python shell
# Generate a file that can be used for input that will contain specified
# number of entries and use the designated random seed, default 0
def gen_input(njobs, seed=0):
    random.seed(seed)
    curStart = 0
    jobList = []
    for i in range(njobs):
        # Generate the priority
        job = [0, 0, 0]
        temp = random.randint(1, 100)
        if(temp <= 40):
            job[0] = random.randint(1, 5)
        elif(temp <= 70):
            job[0] = random.randint(6, 10)
        elif(temp <= 85):
            job[0] = random.randint(11, 15)
        elif(temp <= 95):
            job[0] = random.randint(16, 20)
        else:
            job[0] = 21
            
        # Generate the time to complete the task
        job[1] = random.randrange(10*job[0], 100*job[0], 1)
        
        # Generate the time to start next task based on current start time
        job[2] = curStart
        
        jobList.append(job)
        curStart += random.randint(10, 200)

    with open("test.txt", 'w') as f:
        for job in jobList:
            f.write("{} {} {}\n".format(job[0], job[1], job[2]))
    return 0


main()
