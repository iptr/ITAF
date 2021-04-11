TAIF(Test Automation Interated Framework)V1.0a
======================================

Overview
--------
보안 제품의 Test Suite를 자동화 시키기 위한 프레임워크로 다음의 모듈 및 기능들을 지원한다.
::
    taif manager



Installation
------------

paramiko와 pymysql의 설치는 필요하다.


RPM family (CentOS, RHEL...)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

  yum groupinstall "Development tools"
  yum install zlib-devel bzip2-devel openssl-devel readline-devel ncurses-devel sqlite-devel gdbm-devel db4-devel expat-devel libpcap-devel xz-devel pcre-devel libffi-devel
  yum install net-tools


Required python libraries
^^^^^

::

  pip3 install psutil
  pip3 install paramiko
  pip3 install pymysql


You should then add variables for ``CPPFLAGS`` and ``LDFLAGS`` to your shell environment. This allows ``pythonz`` to find the OpenSSL installed by Homebrew.

::

  export CPPFLAGS="-I/usr/local/opt/openssl/include"
  export LDFLAGS="-L/usr/local/opt/openssl/lib"

Usage
-----

::

  python3 term_tester.py

See the available commands
^^^^^^^^^^^^^^^^^^^^^^^^^^

::


To get help on each individual command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::



Recommended way to use this version of Python
------------------------------------------------------------

For Python <= 3.6
^^^^^^^^^^^^^^^^^
