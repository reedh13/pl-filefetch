#
# filefetch fs ChRIS plugin app
#
# (c) 2021 Fetal-Neonatal Neuroimaging & Developmental Science Center
#                   Boston Children's Hospital
#
#              http://childrenshospital.org/FNNDSC/
#                        dev@babyMRI.org
#

from chrisapp.base import ChrisApp
from github import Github
import requests as rq
import os
import os.path

Gstr_title = r"""

Generate a title from 
http://patorjk.com/software/taag/#p=display&f=Doom&t=filefetch

"""

Gstr_synopsis = """

(Edit this in-line help for app specifics. At a minimum, the 
flags below are supported -- in the case of DS apps, both
positional arguments <inputDir> and <outputDir>; for FS and TS apps
only <outputDir> -- and similarly for <in> <out> directories
where necessary.)

    NAME

       filefetch.py 

    SYNOPSIS

        python filefetch.py                                         \\
            [-h] [--help]                                               \\
            [--json]                                                    \\
            [--man]                                                     \\
            [--meta]                                                    \\
            [--savejson <DIR>]                                          \\
            [-v <level>] [--verbosity <level>]                          \\
            [--version]                                                 \\
            <inputDir>                                                  \\
            <outputDir> 

    BRIEF EXAMPLE

        * Bare bones execution

            docker run --rm -u $(id -u)                             \
                -v $(pwd)/in:/incoming -v $(pwd)/out:/outgoing      \
                fnndsc/pl-filefetch filefetch                        \
                /incoming /outgoing

    DESCRIPTION

        `filefetch.py` ...

    ARGS

        [-h] [--help]
        If specified, show help message and exit.
        
        [--json]
        If specified, show json representation of app and exit.
        
        [--man]
        If specified, print (this) man page and exit.

        [--meta]
        If specified, print plugin meta data and exit.
        
        [--savejson <DIR>] 
        If specified, save json representation file to DIR and exit. 
        
        [-v <level>] [--verbosity <level>]
        Verbosity level for app. Not used currently.
        
        [--version]
        If specified, print version number and exit. 
"""


class Filefetch(ChrisApp):
    """
    An app to fetch files from a GitHub repo andsubsequent plugins.
    """
    PACKAGE                 = __package__
    TITLE                   = 'Fetch files from GitHub'
    CATEGORY                = ''
    TYPE                    = 'fs'
    ICON                    = ''   # url of an icon image
    MIN_NUMBER_OF_WORKERS   = 1    # Override with the minimum number of workers as int
    MAX_NUMBER_OF_WORKERS   = 1    # Override with the maximum number of workers as int
    MIN_CPU_LIMIT           = 1000 # Override with millicore value as int (1000 millicores == 1 CPU core)
    MIN_MEMORY_LIMIT        = 200  # Override with memory MegaByte (MB) limit as int
    MIN_GPU_LIMIT           = 0    # Override with the minimum number of GPUs as int
    MAX_GPU_LIMIT           = 0    # Override with the maximum number of GPUs as int

    # Use this dictionary structure to provide key-value output descriptive information
    # that may be useful for the next downstream plugin. For example:
    #
    # {
    #   "finalOutputFile":  "final/file.out",
    #   "viewer":           "genericTextViewer",
    # }
    #
    # The above dictionary is saved when plugin is called with a ``--saveoutputmeta``
    # flag. Note also that all file paths are relative to the system specified
    # output directory.
    OUTPUT_META_DICT = {}

    def define_parameters(self):
        """
        Define the CLI arguments accepted by this plugin app.
        Use self.add_argument to specify a new app argument.
        """

        self.add_argument('-i', '--inputURL',
                            dest        = 'inputURL',
                            type        = str,
                            optional    = True,
                            help        = 'List of GitHub repo names, subdirectory, or direct URL to file, separated by commas.  (example: -i my_owner/my_repo,https://raw.githubusercontent.com/my_owner/my_repo/my_branch/my_file.jpeg).',
                            default     = ''
                        )
        self.add_argument('-f', '--fileType',
                            dest        = 'fileType',
                            type        = str,
                            default     = '',
                            optional    = True,
                            help        = 'File type(s) to be fetched, separated by commas (example: -t png,jpg,pdf). Fetches all files otherwise.'
                        )
        self.add_argument('-txt', '--txt_url',
                            dest        = 'txt_url',
                            type        = str,
                            optional    = True,
                            help        = 'URL to a raw text file containing a list of URLs to be drawn from.',
                            default     = ''
                        )
        self.add_argument('-t', '--token',
                            dest        = 'token',
                            type        = str,
                            default     = '',
                            optional    = True,
                            help        = 'GitHub personal access token with ONLY(!!!) public_repo permission.'
                        )

    def run(self, options):
        """
        Define the code to be run by this plugin app.
        """

        def mkdir(newdir, mode=0x775):
            """
            works the way a good mkdir should :)
                - already exists, silently complete
                - regular file in the way, raise an exception
                - parent directory(ies) does not exist, make them as well
            """
            if os.path.isdir(newdir):
                pass
            elif os.path.isfile(newdir):
                raise OSError("a file with the same name as the desired " \
                            "dir, '%s', already exists." % newdir)
            else:
                head, tail = os.path.split(newdir)
                if head and not os.path.isdir(head):
                    os.mkdir(head)
                if tail:
                    os.mkdir(newdir)

        def save_file(filename, dir, url, return_name=False):
            """
            Saves a file to the specified directory. Updates the name of the new file if a name collision is detected.

            Param
                filename: attempt to save the file with this name (str)
                dir: save the file to this directory (str)
                url: URL to the raw GitHub file (str)
                return_name: return the name of the saved file (bool)
            Return
                Name of the saved file (str)
            """
            page = rq.get(url)
            start_name = filename
            savepath = dir + '/' + filename
            file_extension = filename.split('.')[-1]
            unsaved = True
            counter = 1
            while unsaved:
                if os.path.exists(savepath):
                    if counter == 1:
                        ext_index = filename.index('.' + file_extension)
                        filename = filename[:ext_index]+'_('+str(counter)+')'+filename[ext_index:]
                    else: 
                        filename = filename.replace('_(' + str(counter-1)+').'+file_extension, 
                                                    '_(' + str(counter)+').'+file_extension, )
                    savepath = dir + '/' + filename
                    counter += 1
                else:
                    file_out = open(savepath, "wb")
                    file_out.write(page.content)
                    file_out.close()
                    if counter != 1:
                        print(f'Collision detected: {start_name} saved as {filename}.')
                    else:
                        print(f'File saved: {filename}')
                    unsaved = False
            if return_name:
                return filename

        def parse_input(url):
            """
            Parses URLs provided by the commandline argument or text file. Returns the GitHub repo, owner, and appropriate subdirectory.

            Parameters
                url: GitHub repo URL in one of the following formats:
                        http(s)://github.com/my_org/my_repo
                        http(s)://github.com/my_org/my_repo/tree/master/my_subdirectory
                        github.com/my_org/my_repo
                        github.com/my_org/my_repo/tree/master/my_subdirectory
                        my_org/my_repo
                        my_org/my_repo/my_subdirectory
            Return
                repo: GitHub repo of interest (PyGithub Repo object)
                owner: name of the owner (str)
                subdir: subdirectory of interest, empty string if not specified (str)
            """
            subdir = ''
            splits = url.split('/')
            if 'https://github.com' in url or 'http://github.com' in url:
                    splits = splits[3:]
            elif 'github.com' in url:
                splits = splits[1:]

            owner = splits[0]
            repo_name = splits[1]

            # Remove /tree/master/ from path if present
            if '/tree/master/' in url:
                i = splits.index(repo_name)
                splits.pop(i+1)
                splits.pop(i+1)

            repo = g.get_repo(owner+'/'+repo_name)
            if len(splits) > 2:
                for i in range(2, len(splits)):
                    subdir = subdir + splits[i] + '/'
                subdir = subdir[:-1]
            return repo, owner, subdir

        print(Gstr_title)
        print('Version: %s' % self.get_version())

        # Create output folder if necessary
        mkdir(options.outputdir)

        my_types = options.fileType.split(',')
        urls = options.inputURL.split(',')

        # Generate URL list from a link to text file
        if options.txt_url != '':
            if not options.txt_url.endswith('.txt'):
                raise Exception("ERROR: Input file must be a .txt file.")
            if urls != ['']:
                raise Exception("ERROR: -i and --inputURL must not be present when using -l and --txt_url")
            txt_name = options.txt_url.split('/')[-1]
            dl_txt = save_file(txt_name, options.outputdir, options.txt_url, True)
            with open(options.outputdir+'/'+dl_txt, 'r') as f:
                urls = f.readlines()
            urls = [url.replace('\n', '') for url in urls]
            os.remove(options.outputdir+'/'+txt_name)

        # Get access to GitHub based on credentials
        if options.token != '':
            g = Github(options.token)
        else:
            g = Github()

        # Search provided URLs for files
        filecount = 0
        for url in urls:
            # Case for direct file link
            if 'raw.githubusercontent.com' in url:
                filename = url.split('/')[-1]
                save_file(filename, options.outputdir, url)
                filecount += 1

            # Case for repo or repo subdirectory
            else:
                repo, owner, subdir = parse_input(url)
                contents = repo.get_contents(subdir)
                while contents:
                    file_content = contents.pop(0)

                    # Recursively explore subdirectories
                    if file_content.type == 'dir':
                        contents.extend(repo.get_contents(file_content.path))
                    # Evaluate a file
                    else:             
                        file_extension = file_content.path.split('.')[-1]

                        # Skip file if it is not of a desired type
                        if my_types != [''] and file_extension not in my_types:
                            continue                

                        # Construct raw url
                        url = 'https://raw.githubusercontent.com/'+owner+'/'+repo.name+'/master/'+file_content.path

                        # Save file and check for filename collisions
                        filename = file_content.path.split('/')[-1]
                        save_file(filename, options.outputdir, url)
                        filecount += 1

        print(f"Files downloaded: {filecount}")

    def show_man_page(self):
        """
        Print the app's man page.
        """
        print(Gstr_synopsis)