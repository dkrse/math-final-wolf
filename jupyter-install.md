
### Phase 1: Prepare the System
Debian restricts global `pip` installs to protect the OS. You must install the Python virtual environment handler first.
```bash
sudo apt update
sudo apt install python3-venv python3-pip
```

### Phase 2: Set Up the Environment
Navigate to your project folder (where your `requirements.txt` is located) and run these commands:

1.  **Create the virtual environment:**
    ```bash
    python3 -m venv .venv
    ```
2.  **Activate it:**
    ```bash
    source .venv/bin/activate
    ```
    *(Your terminal prompt should now show `(.venv)` at the beginning.)*

3.  **Install your libraries:**
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

### Phase 3: Link to Jupyter (The "Kernel" Step)
To make these libraries visible inside the Jupyter interface, you must register this environment as a "Kernel."

1.  **Install the connector:**
    ```bash
    pip install ipykernel
    ```
2.  **Register the Kernel:**
    ```bash
    python3 -m ipykernel install --user --name=my_project_env --display-name "Python (My Project)"
    ```

---

### Phase 4: Select the Environment in Jupyter
Once the steps above are done, you don't need the terminal anymore.

1.  Open your **Jupyter Notebook** in your browser.
2.  Look at the top right corner. It likely says **"Python 3 (ipykernel)"**. Click on it.
3.  A menu will appear. Select **"Python (My Project)"**.
4.  Run your code. The `ModuleNotFoundError` will be gone.

---

### Summary Checklist for Future Use
*   **To add new libraries:** Activate the env (`source .venv/bin/activate`) and run `pip install -r requirements.txt`.
*   **To clean up:** If you want to delete the environment, just delete the `.venv` folder.
*   **Why do this?** It prevents the Debian "externally-managed-environment" error and keeps your system Python "clean."

**Pro Tip:** If you ever forget which environment is active inside a Notebook, run:
```python
import sys
print(sys.executable)
```
It should point to your project folder, not `/usr/bin/python`.
```