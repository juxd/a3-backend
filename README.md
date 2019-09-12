# Backend

## Initial setup
0. Prerequisites: [Check here](https://docs.pipenv.org/en/latest/install/#make-sure-you-ve-got-python-pip)

1. Install Pipenv

MacOS:
```bash
$ brew install pipenv
```

`pip`:
```bash
$ pip install pipenv
```

2. Install the shit

```bash
$ pipenv install --dev
```

3. Get into the environment shell

```bash
$ pipenv shell
```

4. Make sure you've migrated the shit

```bash
$ python3 manage.py migrate
```
5. Run the shit

```bash
$ python3 manage.py runserver
```
