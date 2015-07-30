# iJenkinsCLI

An interactive command line interface for [Jenkins CI](https://jenkins-ci.org/) on the base of [urwid](https://github.com/wardi/urwid) and [autojenkins](https://github.com/txels/autojenkins). For that situation when you dont want to use a browser.

![Example Image](images/ijencinscli.png?raw=true)

## Features

- [x] Interactive browsing of Jobs and high level details in a Jenkins
- [x] Color coded Job status (Successful, Failed, Aborted, etc.)
- [x] Single keyword search, highlight and selection based on job names
- [x] View detailed job information
- [x] Trigger build of a job
- [x] View last build log of a job <3
- [x] Basic VIM like bindings ;)
 
## Usage

1. Clone the current version branch:
  ```bash
  cd /tmp/
  git clone -b 0.1 https://github.com/nkoester/iJenkinsCLI.git && cd iJenkinsCLI
  ```
  
2. Install just like any other python lib:
  ```bash
  export install_destination="/tmp/ijenkinscli"
  mkdir -p $install_destination/lib/python2.7/site-packages/
  export PYTHONPATH=$install_destination/lib/python2.7/site-packages/:$PATH
  export PATH=$install_destination/bin:$PYTHONPATH
  python setup.py install --prefix=$install_destination
  ```
  
3. Run it:
  ```bash
  iJenkinsCLI https://YOUR-SERVER-HERE:8080
  ```

  Or use your credentials:
    ```bash
  iJenkins https://YOUR-SERVER-HERE:8080 --user=jon --password=doe -s
  ```

## Todos

Well, there is always a lot to do... For the first version I was driven by the features. There could be done much much more:

- [ ] Code cleanup. Currently the code is a mess.
- [ ] Improve visual layout and design. Currently a lot is feature driven and not design driven. 
  - [ ] Create a urwid table with some more features
  - [ ] Sort jobs by different columns
  - [ ] Sort jobs by build status
  - [ ] Add some sort of scrollbar
  - [ ] Improve "Job Info" presentation. Currently it is simply displaying the dictionary with all content
  - [ ] Add dialog for help (explaining commands etc.)
  - [ ] Add dialog to login during runtime
- [ ] Expose further features of Jenkins (create job, show build number X, etc.)
- [ ] Parallelise/On demand Jenkins access. If you have many jobs, it may take a while to query all the data
- [ ] Allow different tree organisation (e.g. normal (current), build a tree based on job topology)
- [ ] Many more ...
 
## Feedback

Feel free to contact me if you have any ideas, pull-requests, remarks or feedback! :)
