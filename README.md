# Doppler-OD

Cal Poly CubeSat Lab orbit determination from one-way Doppler using Orekit.

This library is intended to be used in two modes:
1. Before Space-Track TLEs are released, predict CubeSat passes using propagation with pertubations and optionally doppler shift data.
2. After Space-Track TLEs are released, use doppler shift to determine which TLE belongs to PolySat

orekit-data is orekit's data file (obvs) that is needed to run orekit. probably don't touch this unless ur sure

SALE-Doppler is the directory for CSVs of doppler data
TODO: determine CSV format and figure out how to pull CSV of doppler data from SDR

configs holds information about the mission (SAL-E) and the lat/long/alt of g/s. this is needed for doppler stuff.

src/propagate_orbit: propagate orbit with pertubations (drag, J harmonics)

src/doppler_OD: use in combination with propagate_orbit to refine orbit estimation with doppler data (if doppler data is available)

src.which_TLE: use doppler data to determine which space-track TLE belongs to us. filter TLEs from space-track using info in SALE.yaml. BE CAREFUL WITH SPACE-TRACK API REQUESTS, READ THEIR BEST PRACTICES AND DO NOT SPAM API REQUESTS

Best practices:
- USE SI UNITS EVERYWHERE
- call SAL-E "SALE" in variable names and functions and such, the - gets too annoying
- use configs.py to load constants present in configs
- use setup.py to setup orekit directory
- put dependencies in requirements.txt
- include docstrings for all functions you write
- specify variable type for args for all funcs
- structure methods into classes where applicable
- use PascalCase for class names
- use snake_case for variable names and function names
- factor stuff into functions where applicable. if you think others will also use that function, let them know you created it. don't reinvent the wheel. use orekit where u can
- minimize for loops. vectorize everywhere u can. computational cost is not trivial
- push to your own branch. open a pull request when u think ur code is ready to be pushed to main

GitHub Crash course, from Dr. V
# GitHub Vocab for Beginners

-   **Repository (repo):** A main project folder.
-   **Commit:** Think of this as a save button, except GitHub takes a snapshot of your code changes and keeps track of them.
-   **Branch:** A parallel line of work, kind of a copy of your work that you can safely experiment with without breaking others' code..
-   **Remote:** A version of the repo hosted on GitHub.
-   **Main (or master):** The default primary branch (only functional tested code that others can use stays here).
-   **Pull:** Brings the changes from GitHub to your computer.
-   **Push:** Send your local commits/changes to GitHub.

------------------------------------------------------------------------

## Clone (download) an existing GitHub repo

Pick HTTPS unless you've set up SSH keys.

``` bash
git clone https://github.com/dstannar/Doppler-OD.git
```
------------------------------------------------------------------------

## Keep your local copy up to date

Always start your work by updating your main branch:

``` bash
git checkout main          # or: git switch main
git pull origin main       # get the latest from GitHub
```

------------------------------------------------------------------------

## Create and switch to your own branch

Work on a separate branch so you don't break `main`.

**Create a new branch and move onto it (one command):**

``` bash
git switch -c BranchName
# (older syntax) git checkout -b BranchName
```

**Switch between branches later:**

``` bash
git switch main
git switch BranchName
# (older) git checkout main
# (older) git checkout BranchName
```

List branches:

``` bash
git branch            # local branches
git branch -a         # local + remote branches
```

------------------------------------------------------------------------

## See what has changed

``` bash
git status
```
------------------------------------------------------------------------

## Stage and commit (save) your work

**Step 1: Stage everything you changed:**

``` bash
git add .
```

**Step 2: Commit with a message (present tense and meaningful):**

``` bash
git commit -m "Describe what you changed"
```

------------------------------------------------------------------------

## Push your branch to GitHub

First push (sets the remote "upstream" tracking branch):

``` bash
git push -u origin BranchName
```
------------------------------------------------------------------------

## Pull the latest code (sync with teammates)

**From your current branch:**

``` bash
git pull
```

Note: This pulls from the branch you're tracking.

**From main explicitly (recommended before creating new work):**

``` bash
git checkout main      # or: git switch main
git pull origin main
```

------------------------------------------------------------------------

## Bring main's latest into your feature branch

Keep your branch fresh to avoid conflicts:

``` bash
git switch main
git pull origin main
git switch BranchName
git merge main           # or: git rebase main (advanced)
```

Note: If there are **merge conflicts**, Git will mark files and tell you what to do.

------------------------------------------------------------------------

## GitHub Cheat Sheet

``` bash
# 1) Get the latest main
git switch main
git pull origin main

# 2) Create a new branch for your task
git switch -c BranchName

# 3) Work, then stage & commit frequently
git add .
git commit -m "Describe what you changed"

# 4) Push to GitHub
git push -u origin BranchName

# 5) Open a Pull Request on GitHub

# 6) Keep your branch updated while waiting for review
git switch main
git pull origin main
git switch BranchName
git merge main
git push

# 7) After PR is merged, delete your branch (optional)
git branch -d BranchName         # local
git push origin --delete BranchName   # remote
```

