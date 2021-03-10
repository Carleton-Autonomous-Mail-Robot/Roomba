#!/usr/bin/env python

import rospy
from std_msgs.msg import String
from states import *
import time

#Takes delivery requests and environmental data and publishes actions
#Subscribes to inbox and perceptions
#Publishes to actions

targetDestination = "" #target destination is the end goal of the robot and is a global variable
interDestination = ""   # Intermediate destination before the target
currState = WallfollowState()
beginTime = time.time()       # Used for telling how long robot is in certain states
foundWall = True

# Sensor information
currLocation = "A"  # beacons in proximity
currDistance = 10    # distance from/between beacons
currWallDist = 0   # distance from wall
currWallAngle = 0  # angle from wall
currBumper = ""     # bumper state

# Translate the sensor data into actions then publish
def reason(publisher):
    # Setup globals
    global currState
    global targetDestination
    global interDestination
    global beginTime
    global currBumper
    global currDistance
    global currLocation
    global currWallAngle
    global currWallDist
    global foundWall
    
    # Extract the publisher
    (actionPublisher) = publisher
    
    act = ""        # holds the desired action.
    
    # Wall following state
    if str(currState) == 'WallfollowState':
        
        # Are we at our destination?
        if targetDestination == currLocation and currDistance < 10:
            beginTime = time.time()
            currState = currState.on_event('dock')
            
        # Are we at our intermediate destination?
        if interDestination == currLocation and currDistance < 10:
            beginTime = time.time()
            currState = currState.on_event('newdest')
        
        # Bumper status checks
        if currBumper == "unpressed":
            # Since there are no obstacles, check status of robot relative to wall
    
            # Too far from wall, make small correction right. ensure robot angle to wall is proper
            if currWallDist > 25 and currWallAngle > 90:
                act = "sright"
            # Too close to wall, so send bleft msg
            elif currWallDist == 1 and currWallAngle == 90.0:
                if time.time() - beginTime > 0.75:  # consecutive bleft msgs is a problem, so put 0.5s delay between calls
                    act = "bleft"
                    beginTime = time.time()
            # Too close to wall, make small correction left. ensure robot angle to wall is proper
            elif currWallDist < 15 and currWallAngle < 90:
                act = "sleft"
            else:
                act = "forward"
                
        elif currBumper == "Lpressed" or (currBumper == "Rpressed" and currWallDist > 11):
            act = "backward"
            beginTime = time.time()
            foundWall = False
            currState = currState.on_event('bump')      # change to avoidance state
         
    
    # Bumper driven obstacle avoidance state
    elif str(currState) == 'AvoidanceState':
        now = time.time()
        print(now - beginTime)
        
        # Turn 90 degrees left initially
        if now - beginTime < 0.5:
            act = "left"
        else:
            if currBumper == "unpressed":
                # go in arc around obstacle
                if now - beginTime < 13:
                    act = "sright"
                # passed obstacle, ram into wall
                else:
                    act = "forward"
                
                if foundWall:   # change to wallfollowing state
                    currState = currState.on_event('foundwall')
            
            elif currBumper == "Lpressed" or currBumper == "Rpressed":
                # adjust around new obstacle
                if now - beginTime < 12:
                    act = "sleft"
                # its been more than allowed seconds
                else:
                    # Should be back at wall. Rotate and then wallfollow
                    foundWall = True
                    beginTime = now
                    act = "backward"
    
    
    # Robot is in docked state
    elif str(currState) == 'DockState':
        now = time.time()
        if now - beginTime < 0.2:
            act = 'dock'
        elif now - beginTime < 10:
            if not targetDestination == "":
                act = 'undock'
                currState = currState.on_event("newdest")
    
    # Robot has a new destination, adjust direction state
    elif str(currState) == 'InterState':
        # Confirm we are heading in the correct direction
        act = "stop"
        currState = currState.on_event("dirconfirm")
        
    # Publish desired acton
    if not act == '':
        actionPublisher.publish(act)
    


def perceive(data, args):
    # Setup global variables
    global currBumper
    global currDistance
    global currLocation
    global currWallAngle
    global currWallDist
    
    # Extract the publisher and the message data
    (actionPublisher) = args
    message = str(data.data)
    msg = message.split()
    
    # Find perception source and update curr status variables
    if msg[0] == "bumper:":
        currBumper = msg[1]
    elif msg[0] == "distance:":
        currWallDist = float(msg[1])
        currWallAngle = float(msg[3])


def setMission(data, args):
    global targetDestination
    
    #extract the message data
    location = data.data
    targetDestination = location #update targetLocation
    rospy.loginfo("Target Destination updated to " + targetDestination) #log changes
    

# Initialize the node, setup the publisher and subscriber
def rosMain():
    rospy.init_node('Reasoner', anonymous=True)
    actionPublisher = rospy.Publisher('actions', String, queue_size=20)
    rospy.Subscriber('perceptions', String, perceive, (actionPublisher))
    rospy.Subscriber('inbox', String, setMission, (actionPublisher))
    
    rate = rospy.Rate(10)   # 10 Hz
    while not rospy.is_shutdown():
        reason((actionPublisher))
        rate.sleep()

if __name__ == '__main__':
    try:
        rosMain()
    except rospy.ROSInterruptException:
        pass


