import sys
import time
import test_reporter

def run_bc():
    """Run the login script as a function rather than an import"""
    print("Running bc script...")
    # Use execfile equivalent in Python 3
    with open('bc.py', 'r') as f:
        bc_code = compile(f.read(), 'bc.py', 'exec')
        exec(bc_code, globals())
    print("bc script completed successfully.\n")
    # Add a short delay to ensure login is complete
    

def run_login():
    print("Running login script...")
    # Use execfile equivalent in Python 3
    with open('login.py', 'r') as f:
        login_code = compile(f.read(), 'login.py', 'exec')
        exec(login_code, globals())
    print("Login script completed successfully.\n")
    # Add a short delay to ensure login is complete
   

def run_workorder():
    """Run the workorder script as a function rather than an import"""
    print("Running workorder script...")
    # Use execfile equivalent in Python 3
    with open('workorder.py', 'r') as f:
        workorder_code = compile(f.read(), 'workorder.py', 'exec')
        exec(workorder_code, globals())
    print("Workorder script completed successfully.")

def run_mob():
    print("Running mob script...")
    with open('mob.py', 'r') as f:
        mob_code = compile(f.read(), 'mob.py', 'exec')
        exec(mob_code, globals())
    print("mob script completed successfully.")

def run_scripts():
    try:
        run_bc()
        # # Run login first
        # print("\n======= STARTING LOGIN PROCESS =======\n")
        run_login()
        
        # Add a significant delay to ensure the login process is fully complete
        print("\n======= LOGIN COMPLETED, WAITING BEFORE PROCEEDING TO WORKORDER =======\n")
         # 5 second wait to ensure login state is settled
        
        # Then run workorder
        print("\n======= STARTING WORKORDER PROCESS =======\n")
        run_workorder()
        print("\n======= STARTING MOB PROCESS =======\n")
        run_mob()
        
    except Exception as e:
        print(f"\nError occurred: {e}")
        print("Stopping execution.")
    finally:
        # Check if scripts completed successfully
        if 'e' not in locals():
            # No exception occurred, scripts ran successfully
            print("\n======= SCRIPTS COMPLETED SUCCESSFULLY =======")
            print("Keeping browser open for manual interaction...")
            print("Press Enter when you're done to close the browser.")
            input()
            print("\nClosing browser session...")
            print("Browser closed successfully.")
        else:
            # An error occurred, close browser
            print("\nClosing browser session due to error...")
            print("Browser closed.")
        test_reporter.write_html_report()

if __name__ == "__main__":
    run_scripts()
