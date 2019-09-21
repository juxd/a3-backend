# Backend

## Initial setup
0. Prerequisites: [Check here](https://docs.pipenv.org/en/latest/install/#make-sure-you-ve-got-python-pip)

1.  Install Pipenv

    MacOS:
    ```bash
    $ brew install pipenv
    ```

    `pip`:
    ```bash
    $ pip install pipenv
    ```

2.  Install the shit

    ```bash
    $ pipenv install --dev
    ```

3.  Get into the environment shell

    ```bash
    $ pipenv shell
    ```

4.  Make sure you've migrated the shit

    ```bash
    $ python3 manage.py migrate
    ```
5.  Run the shit

    ```bash
    $ python3 manage.py runserver
    ```
    
## Redis setup
This step is necessary to use web sockets. Instructions taken from [here](https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-redis-on-ubuntu-16-04)

1. Download build dependencies
    ```bash
    $ sudo apt-get update
    $ sudo apt-get install build-essential tcl
    ```

2. Download and extract source code  
    Since we won’t need to keep the source code that we’ll compile long term (we can always re-download it), we will build in the /tmp directory. Let’s move there now:
    ```bash
    $ cd /tmp
    ```
    Now, download the latest stable version of Redis. This is always available at a stable download URL:
    ```bash
    $ cd curl -O http://download.redis.io/redis-stable.tar.gz
    ```
    Unpack the tarball by typing:
    ```bash
    $ tar xzvf redis-stable.tar.gz
    ```
    Move into the Redis source directory structure that was just extracted:
    ```bash
    $ cd redis-stable
    ```

3. Build and install redis
    ```bash
    $ make
    $ sudo make install
    ```

4. Launch redis server. Presumedly, this is the step that will always have to be run when restarting the environment.
    ```bash
    $ redis-cli
    ```
    Make sure that the server is opened at port 6379. If it's not, try:
    ```bash
    $ redis-server --port 6379
    ```

