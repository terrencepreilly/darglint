import cProfile
import json
from darglint.docstring.docstring import Docstring

if __name__ == '__main__':
    with open('integration_tests/max_golden.json', 'r') as fin:
        data = json.load(fin)
    assert len(data) == 1
    golden = data[0]
    print(golden['docstring'])
    print()
    assert isinstance(golden['docstring'], str)
    cProfile.run('Docstring.from_google(golden["docstring"])')
