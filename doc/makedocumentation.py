"""This file contains a documentation generating script. Doxygen
is used to do the actual generation, so these functions act primarily to
streamline the process and provide some customizations to the automatically
generated documents
"""

import os, sys
import re
import shutil
import subprocess
import argparse
from datetime import datetime
        
def build(interactive=False):

    if interactive:
        display = lambda txt : raw_input("\n$ %s\r" % txt)
    else:
        display = lambda txt : sys.stdout.write("$ %s\n" % txt)

    display("python make-option-index.py > option_index.txt")
    os.system("python make-option-index.py > option_index.txt")

    # generate pages to be included in general documentation
    mainpage=""
    mainpage+="/**\n\n\\mainpage\n\n"
    for fnm in ["introduction.txt", "installation.txt", "usage.txt", "tutorial.txt", "glossary.txt", "option_index.txt"]:
        page=open(fnm,'r')
        mainpage+=page.read()
    mainpage+="\n\\image latex ForceBalance.pdf \"Logo.\" height=10cm\n\n*/"
    
    with open('mainpage.dox','w') as f:
        f.write(mainpage)

    # generate pages to be included in API documentation
    api=""
    api+="/**\n\n"
    for fnm in ["roadmap.txt"]:
        page=open(fnm,'r')
        api+=page.read()
    api+="\n\n*/"

    with open('api.dox','w') as f:
        f.write(api)
    
    # Run doxygen to generate general documentation
    display("doxygen doxygen.cfg")
    subprocess.call(['doxygen', 'doxygen.cfg'])

    # Run doxygen to generate technical (API) documentation
    display("doxygen api.cfg")
    subprocess.call(['doxygen', 'api.cfg'])
    
    display("python -c 'from makedocumentation import add_tabs; add_tabs()'")
    add_tabs(fnm)
    
    # Compile pdf formats
    display("cp Images/ForceBalance.pdf latex/")
    shutil.copy('Images/ForceBalance.pdf','latex/')
    display("cd latex && make")
    os.chdir('latex')
    subprocess.call(['make'])
    display("cd .. && cp latex/refman.pdf ForceBalance-Manual.pdf")
    os.chdir('..')
    shutil.copy('latex/refman.pdf', 'ForceBalance-Manual.pdf')
    
    display("cp Images/ForceBalance.pdf latex/api/")
    shutil.copy('Images/ForceBalance.pdf','latex/api/')
    display("cd latex/api/ && make")
    os.chdir('latex/api/')
    subprocess.call(['make'])
    display("cd ../.. && cp latex/api/refman.pdf ForceBalance-Manual.pdf")
    os.chdir('../..')
    shutil.copy('latex/api/refman.pdf', 'ForceBalance-API.pdf')

def add_tabs(fnm):
    """Adjust tabs in html version of documentation"""
    for fnm in os.listdir('./html/'):
        if re.match('.*\.html$',fnm):
            fnm = './html/' + fnm
            newfile = []
            installtag = ' class="current"' if fnm.split('/')[-1] == 'installation.html' else ''
            usagetag = ' class="current"' if fnm.split('/')[-1] == 'usage.html' else ''
            tutorialtag = ' class="current"' if fnm.split('/')[-1] == 'tutorial.html' else ''
            glossarytag = ' class="current"' if fnm.split('/')[-1] == 'glossary.html' else ''
            todotag = ' class="current"' if fnm.split('/')[-1] == 'todo.html' else ''
            
            for line in open(fnm):
                newfile.append(line)
                if re.match('.*a href="index\.html"',line):
                    newfile.append('      <li%s><a href="installation.html"><span>Installation</span></a></li>\n' % installtag)
                    newfile.append('      <li%s><a href="usage.html"><span>Usage</span></a></li>\n' % usagetag)
                    newfile.append('      <li%s><a href="tutorial.html"><span>Tutorial</span></a></li>\n' % tutorialtag)
                    newfile.append('      <li%s><a href="glossary.html"><span>Glossary</span></a></li>\n' % glossarytag)
                    newfile.append('      <li><a href="api/roadmap.html"><span>API</span></a></li>\n')
            with open(fnm,'w') as f: f.writelines(newfile)

    for fnm in os.listdir('./html/api/'):
        if re.match('.*\.html$',fnm):
            fnm = './html/api/' + fnm
            newfile=[]
            for line in open(fnm):
                if re.match('.*a href="index\.html"',line):
                    newfile.append('      <li><a href="../index.html"><span>Main Page</span></a></li>\n')
                    newfile.append('      <li ')
                    if re.match('.*roadmap\.html$', fnm): newfile.append('class="current"')
                    newfile.append('><a href="roadmap.html"><span>Project Roadmap</span></a></li>\n')
                else: newfile.append(line)
            with open(fnm,'w') as f: f.writelines(newfile)

def find_forcebalance():
    """try to find forcebalance location in standard python path"""
    forcebalance_dir=""
    try:
        import forcebalance
        forcebalance_dir = forcebalance.__path__[0]
    except:
        print "Unable to find forcebalance directory in PYTHON PATH (Is it installed?)"
        print "Try running forcebalance/setup.py or you can always set the INPUT directory"
        print "manually in api.cfg"
        exit()

    print 'ForceBalance directory is:', forcebalance_dir
    return forcebalance_dir

def find_doxypy():
    """Check if doxypy is in system path or else ask for location of doxypy.py"""
    doxypy_path=""
    try:
        # first check to see if doxypy is in system path
        if subprocess.call(["doxypy", "makedocumentation.py"],stdout=open(os.devnull)): raise OSError()
        doxypy_path="doxypy"
    except OSError: 
        doxypy_path=raw_input("Enter location of doxypy.py: ")
        if not os.path.exists(doxypy_path) or doxypy_path[-9:] != 'doxypy.py':
            print "Invalid path to doxypy"
            exit()
    return doxypy_path

def doxyconf():
    """Try setting values in doxygen config files to match local environment"""
    doxypy_path=""

    # read .cfg, make temp file to edit, replace original when done
    with open('doxygen.cfg', 'r') as fin:
        lines = fin.readlines()

    shutil.copy('doxygen.cfg', 'doxygen.cfg.tmp')

    # make sure FILTER_PATTERNS is set to use doxypy
    with open('doxygen.cfg.tmp', 'w') as fout:
        for line in lines:
            if line.startswith('FILTER_PATTERNS        =') and not re.match(".*doxypy.*", line):
                doxypy_path = find_doxypy()
                option = 'FILTER_PATTERNS        = "*.py=' + doxypy_path + '"\n'
                fout.write(option)
            else:
                fout.write(line)

    shutil.move('doxygen.cfg.tmp', 'doxygen.cfg')

    # same with api.cfg but also check INPUT flag is set to forcebalance location
    # use same doxypy location as in doxygen.cfg
    with open('api.cfg', 'r') as fin:
        lines = fin.readlines()

    shutil.copy('api.cfg','api.cfg.tmp')

    with open('api.cfg.tmp', 'w') as fout:
        for line in lines:
            # I think the find_forcebalance() function needs to be called more often because it was missing the API documentation.
            # if line.startswith('INPUT                  =') and not re.match(".*forcebalance.*|.*src.*", line):
            if line.startswith('INPUT                  ='):
                option = 'INPUT                  = api.dox ' + find_forcebalance() + '\n'
                fout.write(option)
            elif line.startswith('FILTER_PATTERNS        =') and not re.match(".*doxypy.*", line):
                option = 'FILTER_PATTERNS        = "*.py=' + doxypy_path + '"\n'
                fout.write(option)
            else:
                fout.write(line)
    
    shutil.move('api.cfg.tmp', 'api.cfg')
        
def git():
    os.system("git stash")
    print "Switching to doc repository..."
    os.system("git checkout gh-pages")
    os.system("git pull origin gh-pages")
    
    
    print "Applying changes to local repository..."
    os.system('git add ./html *.pdf')
    os.system('git commit -m "Automatic documentation generation at %s on %s"' % (os.environ['HOSTNAME'], datetime.now().strftime("%m-%d-%Y %H:%M")))

    print "\n----Enter username/password to push changes to remote repository or Ctrl-C to abort\n"
    os.system('git push origin gh-pages')
    print
    
    
    print "Returning to branch '%s'..." % branch
    os.system('git reset --hard HEAD')
    os.system('git checkout %s' % branch)
    
    print "Loading master branch stash if necessary..."
    os.system('git stash pop')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument('--clean', action='store_true')
    args = parser.parse_args()
    
    build(interactive = args.interactive)
    
    if args.clean:
        print "Cleaning up..."
        os.system("rm -rf latex option_index.txt api.dox mainpage.dox")   # cleanup
        
    print "Documentation successfully generated"
    
