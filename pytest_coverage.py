import pytest
pytest.main('-v --cov=arbi '
            #'--ignore=tests/unittests/feeds/ '         # 2.5s
            #'--ignore=tests/unittests/execution/ '     # 1.5s
            #'--ignore=tests/unittests/models/ '        # 0.5s
            #'--ignore=tests/unittests/models/test_arbi_spotter.py '    # 16s
            #'--ignore=tests/unittests/tools/ '         # 1.5s
            #'--ignore=tests/unittests/ui/ '            # 0
            #'--ignore=tests/unittests/ui_models/ '     # 0
            #'--ignore=tests/unittests/strats/ '        # 1s
            #'--ignore=tests/unittests/test_arbi_discovery.py '         # 5s
            #'--ignore=tests/unittests/test_arbi_pro.py '          # 6s
            #'--ignore=tests/unittests/test_main.py '                   # 0.5s
            #'--ignore=tests/unittests/test_arbi_summary.py '           # 0
            #'--ignore=tests/unittests/test_utils.py '                  # 0
            #'--ignore=tests/unittests/test_constants.py '              # 0
            )
