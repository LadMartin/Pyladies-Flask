from flask import Flask, request
import re
from datetime import date

app = Flask('my-todos-app')

DATAFILE = 'todos.txt'

'''
obecne by mozna prehlednosti pomohl, kdybychom meli nejakou Tridu
Class item:
    identifier
    is_done
    deadline
    description

a nejaky parser, ktery by umel umel udelat split nad prectenymi daty
a pote nejakou funci na serializaci teto tridy v okamziku kdy ji chceme zapisovat do souboru

ponauceni je vytvorit si nejakou abstrakci, ktera pote umozni snadnejsi pristup.
'''

@app.route('/todo', methods=['POST'])
def add_item():
    identifier, deadline, description = request.data.decode().split(" ", 2)

    if re.match(r"^[a-zA-Z0-9_]+$", identifier) \
            and re.match(r"^([0-9]{4}-[0-9]{2}-[0-9]{2})$", deadline) \
            and re.match(r"^[^\n\r]*$", description):
        with open(DATAFILE, 'a') as f:  # TODO korektni pridani nove radky
            f.write(identifier + " False " + deadline + " " + description + "\n")
        return '', 201
    else:
        return 'Nevalidni vstup', 400  # TODO neměly by být generické responses ve vlastní metodě/objektu/proměnné?


@app.route('/todos')
def get_todos():
    try:
        params = request.args
        lines = ''
        with open(DATAFILE) as f:
            if len(params) == 0:
                return f.read()
            else:
                lines = f.readlines()

        for p in params:
            p_value = params.get(p)
            if p in ["date_from", "date_to", "is_done"]:
                lines = filter_todos(p, p_value, lines)
            elif p == "sort_by" and p_value == "urgency":
                lines = sort_todos(lines)
            elif p == "count" and p_value.isnumeric():
                continue
            else:
                return "Chybné parametry", 400

        if "count" in params:
            lines = head_todos(int(params.get("count")), lines)

        return ''.join(lines)

    except IOError:
        return "Seznam úkolů neexistuje, přidej první úkol", 404


@app.route('/most-urgent')
def get_most_urgent():
    with open(DATAFILE) as f:
        lines = f.readlines()

    lines = filter_todos("date_from", "now", lines)
    lines = sort_todos(lines)
    lines = head_todos(1, lines)

    return ''.join(lines) # TODO jak udělat redirect s parametry? nemělo by to obsahovat i filtr na is_done=False?


@app.route('/todo/<item>', methods=['DELETE'])
def delete_item(item):
    try:
        with open(DATAFILE, "r") as f:
            lines = f.readlines()

        with open(DATAFILE, "w") as f:
            todo_exists = False
            for line in lines:
                identifier = line.strip("\n").split(" ", 1)[0]
                if identifier != item:
                    f.write(line)
                else:
                    todo_exists = True

        if todo_exists:
            return '', 204
        else:
            return 'Úkol není na seznamu', 404

    except IOError:
        return 'Seznam úkolů neexistuje, přidej první úkol', 404


@app.route('/<item>/set-done', methods=['PUT'])
def set_done(item):
    return change_is_done_status(item, "True")


@app.route('/<item>/set-not-done', methods=['PUT'])
def set_not_done(item):
    return change_is_done_status(item, "False")

def change_is_done_status(item, is_done_value):
    try:
        with open(DATAFILE, "r") as f:
            lines = f.readlines()

        todo_exists = False
        for line in lines:
            # Casto se opakuje tento explicitni split. Myslim, ze by se to dalo skryt pod nejakou metodu.
            identifier, _, deadline, description = line.split(" ", 3)
            if identifier == item:
                todo_exists = True
                # zde si popravde nejsem uplne 100% jisty, ze to zmeni value v lines
                line = " ".join([identifier, is_done_value, deadline, description])

        if todo_exists:
            # ale urcite chceme menit data na jednom miste jen v okamziku kdy jsme si jisti ze je co menit
            # na druhou stranu musime byt opatrni, kdyby byly nejakej soubezne dotazy tak by se nam mohlo stat
            # ze nekdo neco prida mezi tim co my zpracovavame tento request a tudiz nove pridane data smazeme
            # avsak synchronizace nebyla predmetem kurzu, pro jednuduchost predpokladame jeden request v jeden cas.
            with open(DATAFILE, "w") as f:
                f.write(lines)
            return '', 204
        else:
            return 'Úkol není na seznamu', 404

    except IOError: # Tento error by se asi dal nejak odchytit globalneji
        return 'Seznam úkolů neexistuje, přidej první úkol', 404


def filter_todos(param, value, todos):
    if value == "now":
        value = str(date.today())

    filtered = []

    if param == "date_from":
        for t in todos:
            # opet split...neni pro ctenare na prvni pohled zrejme co vlastne dostavame
            if t.split(" ", 3)[2] >= value:
                filtered.append(t)
    elif param == "date_to":
        for t in todos:
            if t.split(" ", 3)[2] <= value:
                filtered.append(t)
    else:
        for t in todos:
            if t.split(" ", 3)[1] == value:
                filtered.append(t)

    return filtered


def sort_todos(todos):
    # Opet manualni split
    d = {t.split()[2]: t.strip() for t in todos}
    keysort = sorted([k for k in d])
    return '\n'.join([d[k] for k in keysort])


def head_todos(number_of_todos, todos):
    head = todos[0:number_of_todos]
    return head


if __name__ == '__main__':
    app.run(debug=True)