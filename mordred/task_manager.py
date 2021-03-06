#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#     Luis Cañas-Díaz <lcanas@bitergia.com>
#     Alvaro del Castillo <acs@bitergia.com>
#

import logging
import threading
import time

from grimoire_elk.arthur import get_ocean_backend
from grimoire_elk.utils import get_connector_from_name, get_elastic

logger = logging.getLogger(__name__)

class TasksManager(threading.Thread):
    """
    Class to manage tasks execution

    All tasks in the same task manager will be executed in the same thread
    in a serial way.

    """

    def __init__(self, tasks_cls, backend_name, repos, stopper, conf, timer = 0):
        """
        :tasks_cls : tasks classes to be executed using the backend
        :backend_name: perceval backend name
        :repos: list of repositories to be managed
        :conf: conf for the manager
        """
        super().__init__()  # init the Thread
        self.conf = conf
        self.tasks_cls = tasks_cls  # tasks classes to be executed
        self.tasks = []  # tasks to be executed
        self.backend_name = backend_name
        self.repos = repos
        self.stopper = stopper  # To stop the thread from parent
        self.timer = timer

    def add_task(self, task):
        self.tasks.append(task)

    def run(self):
        logger.debug('Starting Task Manager thread %s', self.backend_name)

        # Configure the tasks
        logger.debug(self.tasks_cls)
        for tc in self.tasks_cls:
            # create the real Task from the class
            task = tc(self.conf)
            task.set_repos(self.repos)
            task.set_backend_name(self.backend_name)
            self.tasks.append(task)

        if not self.tasks:
            logger.debug('Task Manager thread %s without tasks', self.backend_name)

        logger.debug('run(tasks) - run(%s)' % (self.tasks))
        while not self.stopper.is_set():
            # we give 1 extra second to the stopper, so this loop does
            # not finish before it is set.
            time.sleep(1)

            if self.timer > 0:
                time.sleep(self.timer)

            for task in self.tasks:
                task.run()

        logger.debug('Exiting Task Manager thread %s', self.backend_name)

