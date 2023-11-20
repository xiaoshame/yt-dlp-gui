#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Python module to download videos.

This module contains the actual downloaders responsible
for downloading the video files.

"""

from __future__ import unicode_literals

import http.client
import json
import os
import queue
import signal
import subprocess
import time
from threading import Thread
from time import sleep
from urllib.parse import urlparse
import requests

class PipeReader(Thread):
    """Helper class to avoid deadlocks when reading from subprocess pipes.

    This class uses python threads and queues in order to read from subprocess
    pipes in an asynchronous way.

    Attributes:
        WAIT_TIME (float): Time in seconds to sleep.

    Args:
        queue (queue.queue): Python queue to store the output of the subprocess.

    Warnings:
        All the operations are based on 'str' types. The caller has to convert
        the queued items back to 'unicode' if he needs to.

    """

    WAIT_TIME = 0.1

    def __init__(self, queue):
        super(PipeReader, self).__init__()
        self._filedescriptor = None
        self._running = True
        self._queue = queue

        self.start()

    def run(self):
        # Flag to ignore specific lines
        ignore_line = False

        while self._running:
            if self._filedescriptor is not None:
                for line in iter(self._filedescriptor.readline, str('')):
                    if self._filedescriptor is not None:
                        # Ignore ffmpeg stderr
                        if str('ffmpeg version') in line.decode("utf-8"):
                            ignore_line = True

                        if not ignore_line:
                            self._queue.put_nowait(line)

                self._filedescriptor = None
                ignore_line = False

            sleep(self.WAIT_TIME)

    def attach_filedescriptor(self, filedesc):
        """Attach a filedescriptor to the PipeReader. """
        self._filedescriptor = filedesc

    def detach_filedescriptor(self):
        self._filedescriptor = None

    def join(self, timeout=None):
        self._running = False
        super(PipeReader, self).join(timeout)


class YoutubeDLDownloader(object):

    """Python class for downloading videos using youtube-dl & subprocess.

    Attributes:
        OK, ERROR, STOPPED, ALREADY, FILESIZE_ABORT, WARNING (int): Integers
            that describe the return code from the download() method. The
            larger the number the higher is the hierarchy of the code.
            Codes with smaller hierachy cannot overwrite codes with higher
            hierarchy.

    Args:
        youtubedl_path (string): Absolute path to youtube-dl binary.

        data_hook (function): Optional callback function to retrieve download
            process data.

        log_data (function): Optional callback function to write data to
            the log file.

    Warnings:
        The caller is responsible for calling the close() method after he has
        finished with the object in order for the object to be able to properly
        close down itself.

    Example:
        How to use YoutubeDLDownloader from a python script.

            from downloaders import YoutubeDLDownloader

            def data_hook(data):
                print data

            downloader = YoutubeDLDownloader('/usr/bin/youtube-dl', data_hook)

            downloader.download(<URL STRING>, ['-f', 'flv'])

    """

    OK = 0
    WARNING = 1
    ERROR = 2
    FILESIZE_ABORT = 3
    ALREADY = 4
    STOPPED = 5

    def __init__(self, youtubedl_path, data_hook=None, log_data=None):
        self.youtubedl_path = youtubedl_path
        self.data_hook = data_hook
        self.log_data = log_data

        self._return_code = self.OK
        self._proc = None

        self._stderr_queue = queue.Queue()
        self._stderr_reader = PipeReader(self._stderr_queue)

    def download(self, url, options):
        """Download url using given options.

        Args:
            url (string): URL string to download.
            options (list): Python list that contains youtube-dl options.

        Returns:
            An integer that shows the status of the download process.
            There are 6 different return codes.

            OK (0): The download process completed successfully.
            WARNING (1): A warning occured during the download process.
            ERROR (2): An error occured during the download process.
            FILESIZE_ABORT (3): The corresponding url video file was larger or
                smaller from the given filesize limit.
            ALREADY (4): The given url is already downloaded.
            STOPPED (5): The download process was stopped by the user.

        """
        self._return_code = self.OK

        cmd = self._get_cmd(url, options)
        self._create_process(cmd)

        if self._proc is not None:
            self._stderr_reader.attach_filedescriptor(self._proc.stderr)

        while self._proc_is_alive():
            stdout = self._proc.stdout.readline().rstrip()
            if stdout:
                data_dict = extract_data(stdout)
                self._extract_info(data_dict)
                self._hook_data(data_dict)

        # Read stderr after download process has been completed
        # We don't need to read stderr in real time
        while not self._stderr_queue.empty():
            stderr = self._stderr_queue.get_nowait().rstrip()
            if isinstance(stderr, str):
                self._log(stderr)
                
                if self._is_warning(stderr):
                    self._set_returncode(self.WARNING)
                else:
                    self._set_returncode(self.ERROR)
        # Set return code to ERROR if we could not start the download process
        # or the childs return code is greater than zero
        # NOTE: In Linux if the called script is just empty Python exits
        # normally (ret=0), so we cant detect this or similar cases
        # using the code below
        # NOTE: In Unix a negative return code (-N) indicates that the child
        # was terminated by signal N (e.g. -9 = SIGKILL)
        if self._proc is None or self._proc.returncode > 0:
            self._return_code = self.ERROR

        if self._proc is not None and self._proc.returncode > 0:
            self._log('Child process exited with non-zero code: {}'.format(self._proc.returncode))

        self._last_data_hook()

        return self._return_code

    def stop(self):
        """Stop the download process and set return code to STOPPED. """
        if self._proc_is_alive() or self._proc is not None:
            self._stderr_reader.detach_filedescriptor()
            if os.name == 'nt':
                self._proc.terminate()
                self._proc.kill()
                self._proc.returncode = 0
            else:
                os.killpg(self._proc.pid, signal.SIGKILL)

            self._set_returncode(self.STOPPED)

    def close(self):
        """Destructor like function for the object. """
        self._stderr_reader.join()

    def _set_returncode(self, code):
        """Set self._return_code only if the hierarchy of the given code is
        higher than the current self._return_code. """
        if code >= self._return_code:
            self._return_code = code

    def _is_warning(self, stderr):
        return stderr.decode("utf-8").split(':')[0] == 'WARNING'

    def _last_data_hook(self):
        """Set the last data information based on the return code. """
        data_dictionary = {}

        if self._return_code == self.OK:
            data_dictionary['status'] = 'Finished'
        elif self._return_code == self.ERROR:
            data_dictionary['status'] = 'Error'
            data_dictionary['speed'] = ''
            data_dictionary['eta'] = ''
        elif self._return_code == self.WARNING:
            data_dictionary['status'] = 'Warning'
            data_dictionary['speed'] = ''
            data_dictionary['eta'] = ''
        elif self._return_code == self.STOPPED:
            data_dictionary['status'] = 'Stopped'
            data_dictionary['speed'] = ''
            data_dictionary['eta'] = ''
        elif self._return_code == self.ALREADY:
            data_dictionary['status'] = 'Already Downloaded'
        else:
            data_dictionary['status'] = 'Filesize Abort'

        self._hook_data(data_dictionary)

    def _extract_info(self, data):
        """Extract informations about the download process from the given data.

        Args:
            data (dict): Python dictionary that contains different
                keys. The keys are not standar the dictionary can also be
                empty when there are no data to extract. See extract_data().

        """
        if 'status' in data:
            if data['status'] == 'Already Downloaded':
                # Set self._return_code to already downloaded
                # and trash that key
                self._set_returncode(self.ALREADY)
                # data['status'] = None
            if data['status'] == 'Finished':
                self._set_returncode(self.OK)
            if data['status'] == 'Filesize Abort':
                # Set self._return_code to filesize abort
                # and trash that key
                self._set_returncode(self.FILESIZE_ABORT)
                data['status'] = None

    def _log(self, data):
        """Log data using the callback function. """
        if self.log_data is not None:
            self.log_data(data)

    def _hook_data(self, data):
        """Pass data back to the caller. """
        if self.data_hook is not None:
            self.data_hook(data)
    
    def _proc_is_alive(self):
        """Returns True if self._proc is alive else False. """
        if self._proc is None:
            return False
        return self._proc.poll() is None

    def _get_cmd(self, url, options):
        """Build the subprocess command.

        Args:
            url (string): URL string to download.
            options (list): Python list that contains youtube-dl options.

        Returns:
            Python list that contains the command to execute.

        """
        if os.name == 'nt':
            cmd = [self.youtubedl_path] + options + [url]
        else:
            cmd = ['python', self.youtubedl_path] + options + [url]

        return cmd

    def _create_process(self, cmd):
        """Create new subprocess.

        Args:
            cmd (list): Python list that contains the command to execute.

        """
        info = preexec = None

        # Keep a unicode copy of cmd for the log
        ucmd = cmd

        if os.name == 'nt':
            # Hide subprocess window
            info = subprocess.STARTUPINFO()
            info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            # Make subprocess the process group leader
            # in order to kill the whole process group with os.killpg
            preexec = os.setsid

        # Encode command for subprocess
        # Refer to http://stackoverflow.com/a/9951851/35070
        try:
            self._proc = subprocess.Popen(cmd,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          preexec_fn=preexec,
                                          startupinfo=info)
        except (ValueError, OSError) as error:
            self._log('Failed to start process: {}'.format(ucmd))
            self._log(error)


def extract_data(stdout):
    """Extract data from youtube-dl stdout.

    Args:
        stdout (string): String that contains the youtube-dl stdout.

    Returns:
        Python dictionary. The returned dictionary can be empty if there are
        no data to extract else it may contain one or more of the
        following keys:

        'status'         : Contains the status of the download process.
        'path'           : Destination path.
        'extension'      : The file extension.
        'filename'       : The filename without the extension.
        'percent'        : The percentage of the video being downloaded.
        'eta'            : Estimated time for the completion of the download process.
        'speed'          : Download speed.
        'filesize'       : The size of the video file being downloaded.
        'playlist_index' : The playlist index of the current video file being downloaded.
        'playlist_size'  : The number of videos in the playlist.

    """
    # REFACTOR
    def extract_filename(input_data):
        path, fullname = os.path.split(input_data.strip("\""))
        filename, extension = os.path.splitext(fullname)

        return path, filename, extension

    data_dictionary = {}

    if not stdout:
        return data_dictionary

    # We want to keep the spaces in order to extract filenames with
    # multiple whitespaces correctly. We also keep a copy of the old
    # 'stdout' for backward compatibility with the old code
    stdout_with_spaces = stdout.decode("gbk").split(' ')
    stdout = stdout.decode("gbk").split()

    stdout[0] = stdout[0].lstrip('\r')
    if stdout[0] == '[download]':
        data_dictionary['status'] = 'Downloading'

        # Get path, filename & extension
        if stdout[1] == 'Destination:':
            path, filename, extension = extract_filename(' '.join(stdout_with_spaces[2:]))

            data_dictionary['path'] = path
            data_dictionary['filename'] = filename
            data_dictionary['extension'] = extension

        # Get progress info
        if '%' in stdout[1]:
            if stdout[1] == '100%':
                data_dictionary['speed'] = ''
                data_dictionary['eta'] = ''
                data_dictionary['percent'] = '100%'
                data_dictionary['filesize'] = stdout[3]
            else:
                data_dictionary['percent'] = stdout[1]
                data_dictionary['filesize'] = stdout[3]
                data_dictionary['speed'] = stdout[5]
                data_dictionary['eta'] = stdout[7]

        # Get playlist info
        if stdout[1] == 'download' and stdout[2] == 'video':
            data_dictionary['playlist_index'] = stdout[3]
            data_dictionary['playlist_size'] = stdout[5]

        # Remove the 'and merged' part from stdout when using ffmpeg to merge the formats
        if stdout[-3] == 'downloaded' and stdout [-1] == 'merged':
            stdout = stdout[:-2]
            stdout_with_spaces = stdout_with_spaces[:-2]

            data_dictionary['percent'] = '100%'

        # Get file already downloaded status
        if stdout[-1] == 'downloaded':
            data_dictionary['status'] = 'Already Downloaded'
            path, filename, extension = extract_filename(' '.join(stdout_with_spaces[1:-4]))

            data_dictionary['path'] = path
            data_dictionary['filename'] = filename
            data_dictionary['extension'] = extension

        # Get filesize abort status
        if stdout[-1] == 'Aborting.':
            data_dictionary['status'] = 'Filesize Abort'

    elif stdout[0] == '[hlsnative]':
        # native hls extractor
        # see: https://github.com/rg3/youtube-dl/blob/master/youtube_dl/downloader/hls.py#L54
        data_dictionary['status'] = 'Downloading'

        if len(stdout) == 7:
            segment_no = float(stdout[6])
            current_segment = float(stdout[4])

            # Get the percentage
            percent = '{0:.1f}%'.format(current_segment / segment_no * 100)
            data_dictionary['percent'] = percent

    elif stdout[0] == '[ffmpeg]':
        data_dictionary['status'] = 'Post Processing'

        # Get final extension after merging process
        if stdout[1] == 'Merging':
            path, filename, extension = extract_filename(' '.join(stdout_with_spaces[4:]))

            data_dictionary['path'] = path
            data_dictionary['filename'] = filename
            data_dictionary['extension'] = extension

        # Get final extension ffmpeg post process simple (not file merge)
        if stdout[1] == 'Destination:':
            path, filename, extension = extract_filename(' '.join(stdout_with_spaces[2:]))

            data_dictionary['path'] = path
            data_dictionary['filename'] = filename
            data_dictionary['extension'] = extension

        # Get final extension after recoding process
        if stdout[1] == 'Converting':
            path, filename, extension = extract_filename(' '.join(stdout_with_spaces[8:]))

            data_dictionary['path'] = path
            data_dictionary['filename'] = filename
            data_dictionary['extension'] = extension

    elif stdout[0][0] != '[' or stdout[0] == '[debug]':
        pass  # Just ignore this output

    else:
        data_dictionary['status'] = 'Pre Processing'

    return data_dictionary
 
class HaoKanDownloader(object):
    '''文件下载器'''
    OK = 0
    WARNING = 1
    ERROR = 2
    FILESIZE_ABORT = 3
    ALREADY = 4
    STOPPED = 5
 
    def __init__(self, data_hook, log_data):
        '''初始化'''
        self.data_hook = data_hook
        self.log_data = log_data
        self.data = {}
        self._return_code = self.OK
        self.url = None
 
    def download(self,url, options):
        filename,url = self.get_video_info(url)
        self.download_video(url,filename,options)
        return self._return_code
    
    def get_video_info(self,url):
        self.data['status'] = 'Pre Download'
        self._hook_data(self.data)
        base_url = url
        headers = {
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
        }
        try:
            response = requests.get(url=base_url, headers=headers, timeout=5)
            if response.status_code == 200:    
                html = response.text
                start = html.find("window.__PRELOADED_STATE__ = ")
                end = html.find("}};", start)
                json_str = html[start+len("window.__PRELOADED_STATE__ = "):end+2]
                json_data = json.loads(json_str)
                title= json_data['curVideoMeta']['title']
                videoInfo = json_data['curVideoMeta']['clarityUrl']
                url = ''
                for item in videoInfo:
                    if item['key'] == 'sc':
                        url = item['url']
                return title,url
        except Exception as e:
            return '',''
    def download_video(self,url,filename,options):
        conn = None
        if(self.url == "" or filename == ""):
            self.data['status'] = 'Error'
            self._hook_data(self.data)
            self._return_code = self.ERROR
            return
        self.url = urlparse(url)
        if self.url.scheme == 'https':
            conn = http.client.HTTPSConnection(self.url.netloc)
        else:
            conn = http.client.HTTPConnection(self.url.netloc)
        conn.request('GET', self.url.path)
        response = conn.getresponse()
        if response.status == 200:
            self.data['status'] = 'Downloading'
            self._hook_data(self.data)
            total_size = response.getheader('Content-Length')
            file_type = response.getheader('Content-Type').split('/')
            total_size = (int)(total_size)
            if total_size > 0:
                finished_size = 0
                file_path = options[3] % {'title': filename, 'ext': file_type[1]}
                start_time = time.perf_counter()
                size = 0
                file = open(file_path, 'wb')
                if file:
                    while not response.closed:
                        buffers = response.read(1024)
                        file.write(buffers)
                        end_time = time.perf_counter()
                        finished_size += len(buffers)
                        if end_time - start_time > 1:
                            percent = '{0:.1f}%'.format(finished_size / total_size * 100)
                            speed = '{0:.1f}MB/s'.format(((finished_size - size) / (end_time - start_time))/1024/1024)
                            self.data['speed'] = speed
                            self.data['percent'] = percent
                            self._hook_data(self.data)
                            start_time = time.perf_counter()
                            size = finished_size
                        if finished_size >= total_size:
                            break
                    # ... end while statment
                    file.close()
                    self._return_code = self.ALREADY
                else:
                    self.data['status'] = 'Error'
                    self._hook_data(self.data)
                    self._return_code = self.ERROR
                # ... end if statment
            else:
                self.data['status'] = 'Error'
                self._hook_data(self.data)
                self._return_code = self.ERROR
            # ... end if statment
        else:
            self.data['status'] = 'Error'
            self._hook_data(self.data)
            self._return_code = self.ERROR
        # ... end if statment
        conn.close()
        self.data['status'] = 'Already Downloaded'
        self._hook_data(self.data)
    
    def _hook_data(self, data):
        if self.data_hook is not None:
            self.data_hook(data)

    def _log(self, data):
        """Log data using the callback function. """
        if self.log_data is not None:
            self.log_data(data)