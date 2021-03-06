FROM ubuntu:16.04

SHELL ["/bin/bash", "-c"]


#updates repositories in Ubuntu image
RUN apt-get update && \
    apt-get install -y redis-server && \
    apt-get clean

#adds software-properties-common 
RUN apt-get -y install software-properties-common
RUN apt-get -y install curl

#adds required repo

RUN add-apt-repository -y universe && \
    add-apt-repository -y multiverse && \
    add-apt-repository -y restricted



# ROS Kinetic install is based on this tutorial:
# http://wiki.ros.org/kinetic/Installation/Ubuntu
#setup sources.list 
RUN sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'

#Key setup
RUN curl -sSL 'http://keyserver.ubuntu.com/pks/lookup?op=get&search=0xC1CF6E31E6BADE8868B172B4F42ED6FBAB17C654' | apt-key add -

#Update repos
RUN apt-get update

#Download ROS-Base
RUN apt-get -y install ros-kinetic-ros-base



#Sets up enviromental variables
RUN echo "source /opt/ros/kinetic/setup.bash" >> ~/.bashrc && \
    source ~/.bashrc

#Install rosdep
RUN apt install -y python-rosdep python-rosinstall python-rosinstall-generator python-wstool build-essential


#Initialize rosdep
RUN apt install -y python-rosdep
RUN rosdep init
RUN rosdep update



#Install create_autonomy
#https://github.com/AutonomyLab/create_robot
RUN apt-get -y install python-rosdep python-catkin-tools cmake
RUN apt-get -y install git
RUN cd ~
RUN mkdir -p ~/create_ws/src

#Chained command because I need to be within the same dir
RUN cd ~/create_ws && catkin init && \
    cd ~/create_ws/src && \
    git clone https://github.com/autonomylab/create_robot.git && \
    cd create_robot && \
    git checkout kinetic && \
    cd ~/create_ws && \
    rosdep update


RUN source /opt/ros/kinetic/setup.bash && \
    cd ~/create_ws && \
    rosdep install -y --from-paths src -i   && \
    cd ~/create_ws && \
    catkin build

#This is just a dumb argument to rebuild the image before the git clone, change before a docker build if you want to rebuild from
#this point
ARG CAD
#Cloning from Roomba REPO
RUN cd ~/create_ws/src && \
    git clone https://github.com/Carleton-Autonomous-Mail-Robot/roomba.git && \
    cd roomba && \
    git checkout development_docker && \
    cp .bashrc ~/.bashrc && \
    cp .bash_aliases ~/.bash_aliases && \
    source /opt/ros/kinetic/setup.bash && \
    cd ~/create_ws && \
    rosdep update && \
    rosdep install -y --from-paths src -i   && \
    catkin build

RUN apt-get -y install build-essential libpq-dev libssl-dev openssl libffi-dev zlib1g-dev 
RUN apt-get -y install python-pip
RUN add-apt-repository ppa:eugenesan/ppa
RUN apt-get -y update
RUN apt-get install glib2.0 -y
RUN cd ~/create_ws/src/roomba && \
    yes | pip install -r requirements.txt


#Update Python
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get -y install python3-pip python3.7-dev && \
    apt-get -y install python3.7 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 2

RUN pip3 install --upgrade pip


RUN yes | pip3 install virtualenv
RUN yes | pip3 install virtualenvwrapper



#mark scripts as executable
RUN chmod +x ~/create_ws/src/roomba/scripts/*.py




