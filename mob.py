import subprocess
import time
import os
import re

def launch_scrcpy_and_agri_erp(click_work_order=True, click_todo_tab=True, open_latest_workorder=True, click_start_job=True, click_user_and_done=True):
    print("Starting scrcpy and Agrierp launcher")
    
    # Specific path to scrcpy.exe
    scrcpy_path = r"C:\Users\waniaaslam\Downloads\scrcpy-win32-v3.2\scrcpy-win32-v3.2\scrcpy.exe"
    
    try:
        # Check if any device is connected
        device_check = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        if 'device' not in device_check.stdout:
            print("No Android device detected. Please connect a device and try again.")
            print("ADB devices output: \n" + device_check.stdout)
            return
        
        # Launch scrcpy.exe
        print(f"Launching scrcpy from: {scrcpy_path}")
        scrcpy_process = subprocess.Popen([scrcpy_path], 
                                        shell=True,
                                        creationflags=subprocess.CREATE_NEW_CONSOLE)
        
        # Give scrcpy time to start
        print("Waiting for scrcpy to initialize...")
        time.sleep(5)
        
        # Check if scrcpy is running
        if scrcpy_process.poll() is None:  # None means it's still running
            print("scrcpy started successfully!")
        else:
            print("Error: scrcpy failed to start")
            error_output = scrcpy_process.stderr.read() if hasattr(scrcpy_process, 'stderr') and scrcpy_process.stderr else "No error output available"
            print(f"Error details: {error_output}")
            return
        
        # Launch Agrierp on the device
        print("Launching AgriERP-EnHPonFarms-QA using ADB...")
        os.system('adb shell am start -n com.folio3.agrierp.enhponfarmsqa/com.folio3.agrierp.view.activities.MainActivity')
        
        # Wait a moment to see if it worked
        print("Waiting for AgriERP-EnHPonFarms-QA to launch...")
        time.sleep(3)
        
        print("AgriERP-EnHPonFarms-QA should now be launched on your device!")
        print("You should see AgriERP-EnHPonFarms-QA opening in the scrcpy window.")
        
        if click_work_order:
            try:
                print("Waiting for app to load completely...")
                time.sleep(5)
                
                print("Looking for work order card element using ADB...")
                # Get the window hierarchy to find the element
                print("Getting window hierarchy...")
                result = subprocess.run(
                    ['adb', 'shell', 'uiautomator', 'dump'], 
                    capture_output=True, 
                    text=True
                )
                print(f"Dump result: {result.stdout}")
                
                # Pull the UI XML file
                subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'])
                print("Pulled window hierarchy file")
                
                # Now use ADB to click on the element by resource ID
                print("Clicking on work order card...")
                
                # Default coordinates in case we can't find the element
                click_cmd = [
                    'adb', 'shell', 'input', 'tap', '283', '1005'  # Center of the Work Order card based on XML
                ]
                
                # Try to get the actual coordinates of the element
                try:
                    with open('window_dump.xml', 'r', encoding='utf-8') as f:
                        xml_content = f.read()
                        
                        # First try to find by text "Work Order" and then get its parent cardView
                        pattern1 = r'text="Work Order"[^<]*resource-id="com.folio3.agrierp.enhponfarmsqa:id/tv_title"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
                        match1 = re.search(pattern1, xml_content)
                        
                        if match1:
                            # Found the Work Order text, now get its parent cardView
                            print("Found 'Work Order' text element")
                            # Get the bounds of the cardView which is the clickable element
                            pattern2 = r'resource-id="com.folio3.agrierp.enhponfarmsqa:id/cardView"[^<]*class="android.widget.FrameLayout"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
                            match2 = re.search(pattern2, xml_content)
                            
                            if match2:
                                # Calculate center point of the cardView element
                                x1, y1, x2, y2 = map(int, match2.groups())
                                center_x = (x1 + x2) // 2
                                center_y = (y1 + y2) // 2
                                click_cmd = ['adb', 'shell', 'input', 'tap', str(center_x), str(center_y)]
                                print(f"Found Work Order card at coordinates: ({center_x}, {center_y})")
                            else:
                                # If we can't find the cardView, use the text element's coordinates
                                x1, y1, x2, y2 = map(int, match1.groups())
                                center_x = (x1 + x2) // 2
                                center_y = (y1 + y2) // 2
                                click_cmd = ['adb', 'shell', 'input', 'tap', str(center_x), str(center_y)]
                                print(f"Using Work Order text coordinates: ({center_x}, {center_y})")
                        else:
                            # Try a more general approach to find any cardView
                            pattern3 = r'resource-id="com.folio3.agrierp.enhponfarmsqa:id/cardView"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
                            matches = re.finditer(pattern3, xml_content)
                            
                            # Get the first cardView element (which should be the Work Order card based on the XML)
                            for i, match in enumerate(matches):
                                if i == 0:  # First cardView is the Work Order card
                                    x1, y1, x2, y2 = map(int, match.groups())
                                    center_x = (x1 + x2) // 2
                                    center_y = (y1 + y2) // 2
                                    click_cmd = ['adb', 'shell', 'input', 'tap', str(center_x), str(center_y)]
                                    print(f"Found first cardView at coordinates: ({center_x}, {center_y})")
                                    break
                            else:
                                print("Could not find any cardView elements, using default tap position")
                except Exception as e:
                    print(f"Error parsing XML: {e}")
                    print("Using default tap position")
                
                # Execute the tap command
                subprocess.run(click_cmd)
                print("Tap command executed")
                
                print("Successfully clicked on work order card!")
                
                # Wait for the work order screen to load
                print("Waiting for work order screen to load...")
                time.sleep(5)
                
                # Click on the To Do tab if requested
                if click_todo_tab:
                    try:
                        print("Looking for To Do tab...")
                        # Wait a bit longer to ensure the work order screen has fully loaded
                        time.sleep(3)
                        
                        # Get the updated UI hierarchy
                        dump_result = subprocess.run(['adb', 'shell', 'uiautomator', 'dump'], 
                                                  capture_output=True, text=True)
                        print(f"UI dump result: {dump_result.stdout}")
                        
                        pull_result = subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'],
                                                  capture_output=True, text=True)
                        print(f"Pull result: {pull_result.stdout}")
                        
                        # Try multiple approaches to find and click on the To Do tab
                        
                        # Approach 1: Try to find by text
                        todo_coords = find_todo_tab_coordinates()
                        if todo_coords:
                            todo_x, todo_y = todo_coords
                            todo_cmd = ['adb', 'shell', 'input', 'tap', str(todo_x), str(todo_y)]
                            subprocess.run(todo_cmd)
                            print(f"Clicked on To Do tab at coordinates: ({todo_x}, {todo_y})")
                        else:
                            # Approach 2: Try to swipe to reveal tabs if they're in a TabLayout
                            print("Trying to swipe to reveal tabs...")
                            swipe_cmd = ['adb', 'shell', 'input', 'swipe', '500', '400', '100', '400', '300']
                            subprocess.run(swipe_cmd)
                            time.sleep(1)
                            
                            # Approach 3: Try clicking at positions where tabs are commonly located
                            print("Could not find To Do tab, trying common tab positions")
                            
                            # Try left tab position (usually first tab)
                            left_tab_cmd = ['adb', 'shell', 'input', 'tap', '180', '400']
                            subprocess.run(left_tab_cmd)
                            print("Clicked at left tab position")
                            time.sleep(1)
                            
                            # If that didn't work, try another common position
                            center_tab_cmd = ['adb', 'shell', 'input', 'tap', '540', '400']
                            subprocess.run(center_tab_cmd)
                            print("Clicked at center tab position")
                        
                        # Wait after clicking the tab
                        time.sleep(3)
                        
                        # After clicking on the To Do tab, try to open the latest work order
                        if open_latest_workorder:
                            try:
                                print("Looking for the latest work order...")
                                # Wait for the To Do tab content to load
                                time.sleep(2)
                                
                                # Get the updated UI hierarchy
                                subprocess.run(['adb', 'shell', 'uiautomator', 'dump'], capture_output=True, text=True)
                                subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'], capture_output=True, text=True)
                                
                                # Find and click on the latest work order
                                workorder_coords = find_latest_workorder_coordinates()
                                if workorder_coords:
                                    workorder_x, workorder_y = workorder_coords
                                    workorder_cmd = ['adb', 'shell', 'input', 'tap', str(workorder_x), str(workorder_y)]
                                    subprocess.run(workorder_cmd)
                                    print(f"Clicked on latest work order at coordinates: ({workorder_x}, {workorder_y})")
                                    
                                    # Wait for work order details to load
                                    time.sleep(3)
                                    
                                    # Click on Start Job button if requested
                                    if click_start_job:
                                        try:
                                            print("Looking for Start Job button...")
                                            
                                            # Get the updated UI hierarchy
                                            subprocess.run(['adb', 'shell', 'uiautomator', 'dump'], capture_output=True, text=True)
                                            subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'], capture_output=True, text=True)
                                            
                                            # Find and click on the Start Job button at the bottom of the screen
                                            start_job_coords = find_start_job_button_coordinates()
                                            if start_job_coords:
                                                start_x, start_y = start_job_coords
                                                start_cmd = ['adb', 'shell', 'input', 'tap', str(start_x), str(start_y)]
                                                subprocess.run(start_cmd)
                                                print(f"Clicked on Start Job button at coordinates: ({start_x}, {start_y})")
                                                
                                                # Wait for job to start
                                                time.sleep(3)
                                                
                                                # Click on user and then done button if requested
                                                if click_user_and_done:
                                                    try:
                                                        print("Waiting for user selection screen to load...")
                                                        time.sleep(3)

                                                        # Get the updated UI hierarchy for toggle
                                                        subprocess.run(['adb', 'shell', 'uiautomator', 'dump'], capture_output=True, text=True)
                                                        subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'], capture_output=True, text=True)
                                                        # Find toggle coordinates and click to turn ON
                                                        toggle_x, toggle_y = find_toggle_coordinates()
                                                        print(f"Clicking on toggle at position: ({toggle_x}, {toggle_y})")
                                                        toggle_cmd = ['adb', 'shell', 'input', 'tap', str(toggle_x), str(toggle_y)]
                                                        toggle_result = subprocess.run(toggle_cmd, capture_output=True, text=True)
                                                        print(f"Toggle click result: {toggle_result}")
                                                        print(f"Clicked at toggle position ({toggle_x}, {toggle_y})")
                                                        time.sleep(1)

                                                        # Get the updated UI hierarchy again for Done button
                                                        subprocess.run(['adb', 'shell', 'uiautomator', 'dump'], capture_output=True, text=True)
                                                        subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'], capture_output=True, text=True)
                                                        
                                                        # Find Done button coordinates from XML
                                                        done_x, done_y = find_done_button_coordinates()
                                                        print(f"Clicking on Done button at position: ({done_x}, {done_y})")
                                                        done_cmd = ['adb', 'shell', 'input', 'tap', str(done_x), str(done_y)]
                                                        subprocess.run(done_cmd)
                                                        print(f"Clicked on Done button at position: ({done_x}, {done_y})")

                                                        # Wait briefly and then click on user for asset selection
                                                        time.sleep(1)
                                                        print("Getting UI for asset user selection...")
                                                        subprocess.run(['adb', 'shell', 'uiautomator', 'dump'], capture_output=True, text=True)
                                                        subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'], capture_output=True, text=True)
                                                        asset_user_x, asset_user_y = find_user_coordinates()
                                                        print(f"Clicking on user for asset selection at: ({asset_user_x}, {asset_user_y})")
                                                        asset_user_cmd = ['adb', 'shell', 'input', 'tap', str(asset_user_x), str(asset_user_y)]
                                                        subprocess.run(asset_user_cmd)
                                                        print(f"Clicked on user for asset selection at: ({asset_user_x}, {asset_user_y})")

                                                        # Click on Machine tab
                                                        time.sleep(1)
                                                        print("Getting UI for Machine tab...")
                                                        subprocess.run(['adb', 'shell', 'uiautomator', 'dump'], capture_output=True, text=True)
                                                        subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'], capture_output=True, text=True)
                                                        machine_tab_x, machine_tab_y = find_machine_tab_coordinates()
                                                        print(f"Clicking on Machine tab at: ({machine_tab_x}, {machine_tab_y})")
                                                        machine_tab_cmd = ['adb', 'shell', 'input', 'tap', str(machine_tab_x), str(machine_tab_y)]
                                                        subprocess.run(machine_tab_cmd)
                                                        print(f"Clicked on Machine tab at: ({machine_tab_x}, {machine_tab_y})")

                                                        # Select the latest machine
                                                        time.sleep(1)
                                                        print("Getting UI for latest machine selection...")
                                                        subprocess.run(['adb', 'shell', 'uiautomator', 'dump'], capture_output=True, text=True)
                                                        subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'], capture_output=True, text=True)
                                                        latest_machine_x, latest_machine_y = find_latest_machine_coordinates()
                                                        print(f"Clicking on latest machine at: ({latest_machine_x}, {latest_machine_y})")
                                                        latest_machine_cmd = ['adb', 'shell', 'input', 'tap', str(latest_machine_x), str(latest_machine_y)]
                                                        subprocess.run(latest_machine_cmd)
                                                        print(f"Clicked on latest machine at: ({latest_machine_x}, {latest_machine_y})")

                                                        # Click Done button three times
                                                        for i in range(3):
                                                            time.sleep(1)
                                                            print(f"Getting UI for Done button click {i+1}...")
                                                            subprocess.run(['adb', 'shell', 'uiautomator', 'dump'], capture_output=True, text=True)
                                                            subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'], capture_output=True, text=True)
                                                            done_x, done_y = find_done_button_coordinates()
                                                            print(f"Clicking on Done button at: ({done_x}, {done_y}) [Click {i+1}]")
                                                            done_cmd = ['adb', 'shell', 'input', 'tap', str(done_x), str(done_y)]
                                                            subprocess.run(done_cmd)
                                                            print(f"Clicked on Done button at: ({done_x}, {done_y}) [Click {i+1}]")

                                                        # Click Start Job button
                                                        time.sleep(1)
                                                        print("Getting UI for Start Job button...")
                                                        subprocess.run(['adb', 'shell', 'uiautomator', 'dump'], capture_output=True, text=True)
                                                        subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'], capture_output=True, text=True)
                                                        start_job_x, start_job_y = find_start_job_button_coordinates()
                                                        print(f"Clicking on Start Job button at: ({start_job_x}, {start_job_y})")
                                                        start_job_cmd = ['adb', 'shell', 'input', 'tap', str(start_job_x), str(start_job_y)]
                                                        subprocess.run(start_job_cmd)
                                                        print(f"Clicked on Start Job button at: ({start_job_x}, {start_job_y})")

                                                        # Wait for success message after starting job
                                                        print("Waiting for success message after starting job...")
                                                        time.sleep(2)

                                                        # Get the updated UI hierarchy for the success message
                                                        subprocess.run(['adb', 'shell', 'uiautomator', 'dump'], capture_output=True, text=True)
                                                        subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'], capture_output=True, text=True)

                                                        # Find and click the OK button on the success message
                                                        ok_x, ok_y = find_done_button_coordinates()
                                                        print(f"Clicking on OK button at position: ({ok_x}, {ok_y})")
                                                        ok_cmd = ['adb', 'shell', 'input', 'tap', str(ok_x), str(ok_y)]
                                                        subprocess.run(ok_cmd)
                                                        print(f"Clicked on OK button at position: ({ok_x}, {ok_y})")

                                                        # --- New automation steps after Start Job success ---
                                                        try:
                                                            # 1. Click Pause Job button (same logic as Start Job button)
                                                            print("Looking for Pause Job button...")
                                                            # Get the updated UI hierarchy
                                                            subprocess.run(['adb', 'shell', 'uiautomator', 'dump'], capture_output=True, text=True)
                                                            subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'], capture_output=True, text=True)
                                                            # Find and click on the Pause Job button
                                                            pause_job_coords = find_pause_job_button_coordinates()
                                                            if pause_job_coords:
                                                                pause_x, pause_y = pause_job_coords
                                                                pause_cmd = ['adb', 'shell', 'input', 'tap', str(pause_x), str(pause_y)]
                                                                subprocess.run(pause_cmd)
                                                                print(f"Clicked on Pause Job button at coordinates: ({pause_x}, {pause_y})")
                                                                time.sleep(2)
                                                            else:
                                                                print("Could not find Pause Job button coordinates.")

                                                            # 2. On Mark Progress page, click user checkbox and enter progress 1 only once
                                                            print("Mark Progress: Entering progress once")
                                                            subprocess.run(['adb', 'shell', 'uiautomator', 'dump'], capture_output=True, text=True)
                                                            subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'], capture_output=True, text=True)
                                                            user_checkbox_x, user_checkbox_y = find_user_checkbox_coordinates()
                                                            print(f"Clicking on user checkbox at: ({user_checkbox_x}, {user_checkbox_y})")
                                                            subprocess.run(['adb', 'shell', 'input', 'tap', str(user_checkbox_x), str(user_checkbox_y)])
                                                            time.sleep(2)  # Wait for new field to appear

                                                            # Swipe up to bring progress field into view
                                                            print("Swiping up to bring progress field into view...")
                                                            subprocess.run(['adb', 'shell', 'input', 'swipe', '500', '1500', '500', '500', '300'])
                                                            time.sleep(1)

                                                            # Take a new UI dump after field appears
                                                            subprocess.run(['adb', 'shell', 'uiautomator', 'dump'], capture_output=True, text=True)
                                                            subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'], capture_output=True, text=True)

                                                            # Now find and enter progress in the correct field
                                                            progress_field_x, progress_field_y = find_progress_field_coordinates()
                                                            print(f"Clicking on progress field at: ({progress_field_x}, {progress_field_y})")
                                                            subprocess.run(['adb', 'shell', 'input', 'tap', str(progress_field_x), str(progress_field_y)])
                                                            time.sleep(1)
                                                            print("Entering progress value: 1")
                                                            subprocess.run(['adb', 'shell', 'input', 'text', '1'])
                                                            time.sleep(1)
                                                            subprocess.run(['adb', 'shell', 'input', 'keyevent', '66'])
                                                            time.sleep(1)

                                                            # Wait for UI to update before clicking Material tab
                                                            time.sleep(1)
                                                            # Take a new UI dump before clicking Material tab
                                                            subprocess.run(['adb', 'shell', 'uiautomator', 'dump'], capture_output=True, text=True)
                                                            subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'], capture_output=True, text=True)

                                                            # Now find and click Material tab
                                                            material_tab_x, material_tab_y = find_material_tab_coordinates()
                                                            if material_tab_x and material_tab_y:
                                                                subprocess.run(['adb', 'shell', 'input', 'tap', str(material_tab_x), str(material_tab_y)])
                                                                print(f"Clicked on Material tab at: ({material_tab_x}, {material_tab_y})")
                                                                time.sleep(1)
                                                                # Swipe up to bring material progress field into view
                                                                print("Swiping up to bring material progress field into view...")
                                                                subprocess.run(['adb', 'shell', 'input', 'swipe', '500', '1500', '500', '500', '300'])
                                                                time.sleep(1)
                                                                # Take a new UI dump
                                                                subprocess.run(['adb', 'shell', 'uiautomator', 'dump'], capture_output=True, text=True)
                                                                subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'], capture_output=True, text=True)
                                                                # Now find and enter 20 in the first material progress field
                                                                first_material_x, first_material_y = find_first_material_progress_field_coordinates()
                                                                subprocess.run(['adb', 'shell', 'input', 'tap', str(first_material_x), str(first_material_y)])
                                                                time.sleep(1)
                                                                subprocess.run(['adb', 'shell', 'input', 'text', '20'])
                                                                time.sleep(1)
                                                                subprocess.run(['adb', 'shell', 'input', 'keyevent', '66'])
                                                                time.sleep(1)
                                                            else:
                                                                print("[DEBUG] Material tab not found!")

                                                            # 4. Enter 20 in first material progress field
                                                            print("Entering 20 in first material progress field...")
                                                            first_material_x, first_material_y = find_first_material_progress_field_coordinates()
                                                            subprocess.run(['adb', 'shell', 'input', 'tap', str(first_material_x), str(first_material_y)])
                                                            time.sleep(1)
                                                            subprocess.run(['adb', 'shell', 'input', 'text', '20'])
                                                            time.sleep(1)
                                                            subprocess.run(['adb', 'shell', 'input', 'keyevent', '66'])
                                                            time.sleep(1)

                                                            # 5. Click Pause Job button again
                                                            print("Clicking Pause Job button again...")
                                                            subprocess.run(['adb', 'shell', 'uiautomator', 'dump'], capture_output=True, text=True)
                                                            subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'], capture_output=True, text=True)
                                                            pause_x, pause_y = find_pause_job_button_coordinates()
                                                            subprocess.run(['adb', 'shell', 'input', 'tap', str(pause_x), str(pause_y)])
                                                            print("Pause Job button clicked again.")
                                                            time.sleep(2)
                                                        except Exception as e:
                                                            print(f"Error in post-Start Job automation: {e}")

                                                        # --- End of new automation steps ---
                                                    except Exception as e:
                                                        print(f"Error clicking on toggle or done button: {e}")
                                            else:
                                                # If we couldn't find the button by ID, try clicking at the bottom center of the screen
                                                # This is where the Start Job button is located based on the XML
                                                print("Could not find Start Job button by ID, clicking at bottom center")
                                                bottom_center_cmd = ['adb', 'shell', 'input', 'tap', '540', '1970']
                                                subprocess.run(bottom_center_cmd)
                                                print("Clicked at bottom center where Start Job button should be")
                                                time.sleep(3)
                                        except Exception as e:
                                            print(f"Error clicking on Start Job button: {e}")
                                else:
                                    print("Could not find latest work order, trying to click on first item in list")
                                    # Try clicking at a position where the first item in a list would typically be
                                    first_item_cmd = ['adb', 'shell', 'input', 'tap', '540', '600']
                                    subprocess.run(first_item_cmd)
                                    print("Clicked at position of likely first work order item")
                                    time.sleep(3)
                            except Exception as e:
                                print(f"Error opening latest work order: {e}")
                    except Exception as e:
                        print(f"Error clicking on To Do tab: {e}")
                
                # Keep the session open for a while after clicking
                time.sleep(5)
                
            except Exception as e:
                print(f"Error during ADB automation: {e}")
        
        # Keep the script running to keep scrcpy open
        print("Keeping session open for 60 seconds...")
        print("Press Ctrl+C to exit early")
        time.sleep(60)
        
    except KeyboardInterrupt:
        print("Script interrupted by user")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Session ended")

def find_work_order_card_coordinates():
    """Find the coordinates of the Work Order card from the UI dump"""
    try:
        # Dump UI hierarchy
        subprocess.run(['adb', 'shell', 'uiautomator', 'dump'], capture_output=True)
        subprocess.run(['adb', 'pull', '/sdcard/window_dump.xml', '.'])
        
        with open('window_dump.xml', 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Look for the Work Order card by finding the cardView containing "Work Order" text
        # Based on the XML structure we've seen
        work_order_bounds = None
        
        # First find the text element with "Work Order"
        text_match = re.search(r'text="Work Order"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if text_match:
            print("Found 'Work Order' text element")
            
            # Find the first cardView element which should be the Work Order card
            card_match = re.search(r'resource-id="com.folio3.agrierp.enhponfarmsqa:id/cardView"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
            if card_match:
                x1, y1, x2, y2 = map(int, card_match.groups())
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                return center_x, center_y
        
        # If we couldn't find it, return default coordinates
        return 283, 1005  # Center of the Work Order card based on XML
    except Exception as e:
        print(f"Error finding Work Order card: {e}")
        return 283, 1005  # Default coordinates

def find_todo_tab_coordinates():
    """Find the coordinates of the To Do tab from the UI dump"""
    try:
        with open('window_dump.xml', 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Try multiple patterns to find the To Do tab
        
        # Pattern 1: Direct match for "To Do" text
        todo_match = re.search(r'text="To Do"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if todo_match:
            x1, y1, x2, y2 = map(int, todo_match.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"Found 'To Do' text at coordinates: ({center_x}, {center_y})")
            return center_x, center_y
            
        # Pattern 2: Try "TODO" (all caps)
        todo_match2 = re.search(r'text="TODO"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if todo_match2:
            x1, y1, x2, y2 = map(int, todo_match2.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"Found 'TODO' text at coordinates: ({center_x}, {center_y})")
            return center_x, center_y
            
        # Pattern 3: Try "ToDo" (camel case)
        todo_match3 = re.search(r'text="ToDo"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if todo_match3:
            x1, y1, x2, y2 = map(int, todo_match3.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"Found 'ToDo' text at coordinates: ({center_x}, {center_y})")
            return center_x, center_y
        
        # Pattern 4: Look for TabLayout
        tab_match = re.search(r'resource-id="com.folio3.agrierp.enhponfarmsqa:id/tabLayout"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if tab_match:
            # Found the tab layout, now try to find the first tab (which is likely To Do)
            x1, y1, x2, y2 = map(int, tab_match.groups())
            # Calculate position of first tab (approximately 1/4 of the way from the left)
            tab_width = x2 - x1
            first_tab_x = x1 + (tab_width // 4)
            first_tab_y = (y1 + y2) // 2
            print(f"Found tab layout, estimating first tab at: ({first_tab_x}, {first_tab_y})")
            return first_tab_x, first_tab_y
            
        # Pattern 5: Look for any TabItem
        tab_item_match = re.search(r'class="android.widget.TabItem"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if tab_item_match:
            x1, y1, x2, y2 = map(int, tab_item_match.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"Found TabItem at coordinates: ({center_x}, {center_y})")
            return center_x, center_y
            
        # Pattern 6: Look for any selected tab
        selected_tab_match = re.search(r'selected="true"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if selected_tab_match:
            x1, y1, x2, y2 = map(int, selected_tab_match.groups())
            # We want to click to the left of the selected tab to find the To Do tab
            center_x = x1 - 200  # Move 200 pixels to the left
            center_y = (y1 + y2) // 2
            print(f"Found selected tab, trying position to the left: ({center_x}, {center_y})")
            return center_x, center_y
        
        # If we couldn't find it, return None
        print("Could not find To Do tab using any pattern")
        return None
    except Exception as e:
        print(f"Error finding To Do tab: {e}")
        return None

def find_latest_workorder_coordinates():
    """Find the coordinates of the latest created work order in the To Do tab"""
    try:
        with open('window_dump.xml', 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Try multiple patterns to find the latest work order
        
        # Pattern 1: Look for RecyclerView which likely contains the work orders
        recycler_match = re.search(r'class="androidx.recyclerview.widget.RecyclerView"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if recycler_match:
            # Found the RecyclerView, now find the first item which is likely the latest work order
            x1, y1, x2, y2 = map(int, recycler_match.groups())
            # Calculate position of first item (center of the RecyclerView, but closer to the top)
            center_x = (x1 + x2) // 2
            first_item_y = y1 + 100  # 100 pixels from the top of the RecyclerView
            print(f"Found RecyclerView, estimating first item at: ({center_x}, {first_item_y})")
            return center_x, first_item_y
        
        # Pattern 2: Look for any ListView
        list_match = re.search(r'class="android.widget.ListView"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if list_match:
            x1, y1, x2, y2 = map(int, list_match.groups())
            center_x = (x1 + x2) // 2
            first_item_y = y1 + 100
            print(f"Found ListView, estimating first item at: ({center_x}, {first_item_y})")
            return center_x, first_item_y
        
        # Pattern 3: Look for any item with "Work Order" or "WO" in the text
        wo_match = re.search(r'text="[^"]*Work Order[^"]*"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if wo_match:
            x1, y1, x2, y2 = map(int, wo_match.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"Found work order item at: ({center_x}, {center_y})")
            return center_x, center_y
        
        # Pattern 4: Look for any item with a date format (likely a work order date)
        date_match = re.search(r'text="\d{2}/\d{2}/\d{4}"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if date_match:
            x1, y1, x2, y2 = map(int, date_match.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"Found date item (likely work order) at: ({center_x}, {center_y})")
            return center_x, center_y
        
        # Pattern 5: Look for any clickable item in the middle of the screen
        clickable_match = re.search(r'clickable="true"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if clickable_match:
            x1, y1, x2, y2 = map(int, clickable_match.groups())
            # Only consider items in the middle section of the screen (not navigation or tabs)
            if y1 > 500 and y2 < 1800:  # Typical content area
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                print(f"Found clickable item in content area at: ({center_x}, {center_y})")
                return center_x, center_y
        
        # If we couldn't find anything specific, return a default position in the content area
        print("Could not find latest work order, using default position")
        return 540, 700  # Center horizontally, upper part of content area vertically
    except Exception as e:
        print(f"Error finding latest work order: {e}")
        return 540, 700  # Default fallback position

def find_start_job_button_coordinates():
    """Find the coordinates of the Start Job button in the work order details screen"""
    try:
        with open('window_dump.xml', 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Try multiple patterns to find the Start Job button
        
        # Pattern 1: Look for the btnJob ID at the bottom of the screen
        btn_job_match = re.search(r'resource-id="com.folio3.agrierp.enhponfarmsqa:id/btnJob"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if btn_job_match:
            x1, y1, x2, y2 = map(int, btn_job_match.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"Found Start Job button with ID 'btnJob' at coordinates: ({center_x}, {center_y})")
            return center_x, center_y
        
        # Pattern 2: Direct match for "Start Job" text
        start_job_match = re.search(r'text="Start Job"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if start_job_match:
            x1, y1, x2, y2 = map(int, start_job_match.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"Found 'Start Job' text at coordinates: ({center_x}, {center_y})")
            return center_x, center_y
        
        # Pattern 3: Look for any text element with "Start Job" at the bottom of the screen
        bottom_start_job_match = re.search(r'text="Start Job"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if bottom_start_job_match:
            x1, y1, x2, y2 = map(int, bottom_start_job_match.groups())
            # Only consider elements at the bottom of the screen
            if y1 > 1800:  # Bottom of the screen
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                print(f"Found 'Start Job' text at bottom of screen: ({center_x}, {center_y})")
                return center_x, center_y
        
        # Pattern 4: Look for any clickable TextView at the bottom of the screen
        bottom_textview_match = re.search(r'class="android.widget.TextView"[^<]*clickable="true"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if bottom_textview_match:
            x1, y1, x2, y2 = map(int, bottom_textview_match.groups())
            # Only consider elements at the bottom of the screen
            if y1 > 1800:  # Bottom of the screen
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                print(f"Found clickable TextView at bottom of screen: ({center_x}, {center_y})")
                return center_x, center_y
        
        # Pattern 5: Look for any element at the very bottom of the screen that's clickable
        bottom_element_match = re.search(r'bounds="\[(\d+),(1[89]\d\d)\]\[(\d+),(2\d\d\d)\]"[^<]*clickable="true"', xml_content)
        if bottom_element_match:
            x1, y1, x2, y2 = map(int, bottom_element_match.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"Found clickable element at very bottom of screen: ({center_x}, {center_y})")
            return center_x, center_y
        
        # If we couldn't find the button, return a default position at the bottom center of the screen
        # This is where the Start Job button is typically located
        print("Could not find Start Job button, using default position at bottom center")
        return 540, 1970  # Center horizontally, very bottom of screen vertically
    except Exception as e:
        print(f"Error finding Start Job button: {e}")
        return 540, 1970  # Default fallback position

def find_user_coordinates():
    """Find the coordinates of a user in the user selection screen"""
    # For this function, we're going to use fixed positions that are more likely to work
    # based on common UI patterns for user selection screens
    print("Using fixed position for user selection")
    return 540, 600  # Center horizontally, upper part of screen vertically

def find_done_button_coordinates():
    """Find the coordinates of the Done button"""
    try:
        with open('window_dump.xml', 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Try multiple patterns to find the Done button
        
        # Pattern 1: Direct match for "Done" text
        done_match = re.search(r'text="Done"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if done_match:
            x1, y1, x2, y2 = map(int, done_match.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"Found 'Done' text at coordinates: ({center_x}, {center_y})")
            return center_x, center_y
        
        # Pattern 2: Look for "OK" text (another possible label)
        ok_match = re.search(r'text="OK"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if ok_match:
            x1, y1, x2, y2 = map(int, ok_match.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"Found 'OK' text at coordinates: ({center_x}, {center_y})")
            return center_x, center_y
        
        # Pattern 3: Look for any button at the bottom right of the screen
        bottom_right_button = re.search(r'class="android.widget.Button"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if bottom_right_button:
            x1, y1, x2, y2 = map(int, bottom_right_button.groups())
            # Only consider buttons in the bottom right part of the screen
            if y1 > 1500 and x1 > 540:  # Bottom right of the screen
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                print(f"Found button in bottom right at: ({center_x}, {center_y})")
                return center_x, center_y
        
        # Pattern 4: Look for any clickable TextView at the bottom right
        bottom_right_text = re.search(r'class="android.widget.TextView"[^<]*clickable="true"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if bottom_right_text:
            x1, y1, x2, y2 = map(int, bottom_right_text.groups())
            # Only consider text in the bottom right part of the screen
            if y1 > 1500 and x1 > 540:  # Bottom right of the screen
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                print(f"Found clickable text in bottom right at: ({center_x}, {center_y})")
                return center_x, center_y
        
        # If we couldn't find the button, return a default position at the bottom right of the screen
        print("Could not find Done button, using default position")
        return 900, 1970  # Bottom right of screen
    except Exception as e:
        print(f"Error finding Done button: {e}")
        return 900, 1970  # Default fallback position

def find_toggle_coordinates():
    """Find the coordinates of the toggle button in the user selection screen"""
    try:
        with open('window_dump.xml', 'r', encoding='utf-8') as f:
            xml_content = f.read()
        # Look for the specific resource-id for the toggle
        toggle_match = re.search(r'resource-id="com.folio3.agrierp.enhponfarmsqa:id/switchSelectAll"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if toggle_match:
            x1, y1, x2, y2 = map(int, toggle_match.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"Found switchSelectAll toggle at coordinates: ({center_x}, {center_y})")
            return center_x, center_y
        # Fallback: Try to find a CompoundButton
        compound_match = re.search(r'class="android.widget.CompoundButton"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if compound_match:
            x1, y1, x2, y2 = map(int, compound_match.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"Found CompoundButton at coordinates: ({center_x}, {center_y})")
            return center_x, center_y
        # Default position if not found
        print("Could not find toggle, using default position (900, 600)")
        return 900, 600
    except Exception as e:
        print(f"Error finding toggle: {e}")
        return 900, 600

def find_machine_tab_coordinates():
    """Find the coordinates of the Machine tab"""
    try:
        with open('window_dump.xml', 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Look for the Machine tab by finding the tab with "Machine" text
        tab_match = re.search(r'text="Machine"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if tab_match:
            x1, y1, x2, y2 = map(int, tab_match.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"Found Machine tab at coordinates: ({center_x}, {center_y})")
            return center_x, center_y
        
        # If we couldn't find it, return None
        print("Could not find Machine tab")
        return None
    except Exception as e:
        print(f"Error finding Machine tab: {e}")
        return None

def find_latest_machine_coordinates():
    """Find the coordinates of the first machine in the Machine tab"""
    try:
        with open('window_dump.xml', 'r', encoding='utf-8') as f:
            xml_content = f.read()
        # Look for the machine list by ListView or RecyclerView
        machine_match = re.search(r'class="android.widget.ListView"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if machine_match:
            x1, y1, x2, y2 = map(int, machine_match.groups())
            # Calculate position of the first item (center of the ListView, but closer to the top)
            center_x = (x1 + x2) // 2
            first_item_y = y1 + 100  # 100 pixels from the top of the ListView
            print(f"Found Machine tab, estimating first item at: ({center_x}, {first_item_y})")
            return center_x, first_item_y
        # Try RecyclerView as fallback
        recycler_match = re.search(r'class="androidx.recyclerview.widget.RecyclerView"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if recycler_match:
            x1, y1, x2, y2 = map(int, recycler_match.groups())
            center_x = (x1 + x2) // 2
            first_item_y = y1 + 100
            print(f"Found RecyclerView, estimating first item at: ({center_x}, {first_item_y})")
            return center_x, first_item_y
        # If we couldn't find anything specific, return a default position in the Machine tab
        print("Could not find first machine, using default position")
        return 540, 700  # Center horizontally, upper part of Machine tab vertically
    except Exception as e:
        print(f"Error finding first machine: {e}")
        return 540, 700  # Default fallback position

def find_pause_job_button_coordinates():
    """Find the coordinates of the Pause Job button from the UI dump, with debug output and fallback to class/clickable search."""
    try:
        with open('window_dump.xml', 'r', encoding='utf-8') as f:
            xml_content = f.read()
        # Debug: print a snippet if 'Pause' is found
        pause_snippet = ''
        for line in xml_content.splitlines():
            if 'Pause' in line or 'pause' in line:
                pause_snippet += line.strip() + '\n'
        if pause_snippet:
            print("[DEBUG] Found lines with 'Pause':\n" + pause_snippet)
        else:
            print("[DEBUG] No lines with 'Pause' found in XML.")
        # Try to find by text (case-insensitive)
        pause_match = re.search(r'text="([Pp]ause[^\"]*)"[^<]*bounds="\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]"', xml_content)
        if pause_match:
            print(f"[DEBUG] Matched Pause Job text: {pause_match.group(1)}")
            x1, y1, x2, y2 = map(int, pause_match.groups()[1:])
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"Found Pause Job button at: ({center_x}, {center_y})")
            return center_x, center_y
        # Fallback: try to find any clickable button at the bottom of the screen
        button_match = re.search(r'class="android.widget.Button"[^<]*clickable="true"[^<]*bounds="\\[(\\d+),(1[5-9]\\d{2}|2\\d{3})\\]\\[(\\d+),(2\\d{3})\\]"', xml_content)
        if button_match:
            print("[DEBUG] Fallback: found clickable android.widget.Button at bottom of screen.")
            x1, y1, x2, y2 = map(int, button_match.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"Found fallback Pause Job button at: ({center_x}, {center_y})")
            return center_x, center_y
        # Fallback: try any clickable element at the bottom
        clickable_match = re.search(r'clickable="true"[^<]*bounds="\\[(\\d+),(1[5-9]\\d{2}|2\\d{3})\\]\\[(\\d+),(2\\d{3})\\]"', xml_content)
        if clickable_match:
            print("[DEBUG] Fallback: found generic clickable element at bottom of screen.")
            x1, y1, x2, y2 = map(int, clickable_match.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"Found fallback clickable Pause Job at: ({center_x}, {center_y})")
            return center_x, center_y
        print("[DEBUG] Could not find Pause Job button by text, class, or clickable property. Using default.")
        return 900, 1970
    except Exception as e:
        print(f"Error finding Pause Job button: {e}")
        return 900, 1970

def find_user_checkbox_coordinates():
    """Find the coordinates of the user checkbox on Mark Progress page"""
    try:
        with open('window_dump.xml', 'r', encoding='utf-8') as f:
            xml_content = f.read()
        # Try to find by class or resource-id
        checkbox_match = re.search(r'class="android.widget.CheckBox"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
        if checkbox_match:
            x1, y1, x2, y2 = map(int, checkbox_match.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"Found user checkbox at: ({center_x}, {center_y})")
            return center_x, center_y
        # Fallback: left side
        return 100, 600
    except Exception as e:
        print(f"Error finding user checkbox: {e}")
        return 100, 600

def find_progress_field_coordinates():
    """Find the coordinates of the progress input field on Mark Progress page, selecting the bottom-most EditText."""
    try:
        with open('window_dump.xml', 'r', encoding='utf-8') as f:
            xml_content = f.read()
        # Find all EditText fields
        edittext_matches = list(re.finditer(r'class="android.widget.EditText"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content))
        print(f"[DEBUG] Found {len(edittext_matches)} EditText fields.")
        bottom_most = None
        max_y2 = -1
        for idx, match in enumerate(edittext_matches):
            x1, y1, x2, y2 = map(int, match.groups())
            print(f"[DEBUG] EditText {idx+1}: bounds=({x1},{y1})-({x2},{y2})")
            if y2 > max_y2:
                max_y2 = y2
                bottom_most = match
        if bottom_most:
            x1, y1, x2, y2 = map(int, bottom_most.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"[DEBUG] Using bottom-most EditText as progress field at: ({center_x}, {center_y})")
            return center_x, center_y
        else:
            print("[DEBUG] No EditText fields found, using default progress field position.")
            return 540, 900
    except Exception as e:
        print(f"Error finding progress field: {e}")
        return 540, 900

def find_material_tab_coordinates():
    """Find the coordinates of the Materials tab next to Progress tab."""
    try:
        with open('window_dump.xml', 'r', encoding='utf-8') as f:
            xml_content = f.read()
        # Find all tab nodes with text
        tab_matches = list(re.finditer(r'text="([^"]+)"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content))
        progress_coords = None
        material_coords = None
        for idx, match in enumerate(tab_matches):
            tab_text = match.group(1).strip().lower()
            x1, y1, x2, y2 = map(int, match.groups()[1:])
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            if tab_text == 'progress':
                print(f"[DEBUG] Found Progress tab at: ({center_x}, {center_y})")
                progress_coords = (center_x, center_y)
            if tab_text == 'materials':
                print(f"[DEBUG] Found Materials tab at: ({center_x}, {center_y})")
                material_coords = (center_x, center_y)
        if material_coords:
            return material_coords
        print("[DEBUG] Materials tab not found, using default position.")
        return 900, 400
    except Exception as e:
        print(f"Error finding Materials tab: {e}")
        return 900, 400

def find_first_material_progress_field_coordinates():
    """Find the coordinates of the bottom-most EditText (material progress field) after Material tab is selected."""
    try:
        with open('window_dump.xml', 'r', encoding='utf-8') as f:
            xml_content = f.read()
        edittext_matches = list(re.finditer(r'class="android.widget.EditText"[^<]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content))
        print(f"[DEBUG] Found {len(edittext_matches)} EditText fields (Material tab).")
        bottom_most = None
        max_y2 = -1
        for idx, match in enumerate(edittext_matches):
            x1, y1, x2, y2 = map(int, match.groups())
            print(f"[DEBUG] EditText {idx+1}: bounds=({x1},{y1})-({x2},{y2})")
            if y2 > max_y2:
                max_y2 = y2
                bottom_most = match
        if bottom_most:
            x1, y1, x2, y2 = map(int, bottom_most.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            print(f"[DEBUG] Using bottom-most EditText as material progress field at: ({center_x}, {center_y})")
            return center_x, center_y
        else:
            print("[DEBUG] No EditText fields found, using default material progress field position.")
            return 540, 1200
    except Exception as e:
        print(f"Error finding first material progress field: {e}")
        return 540, 1200

if __name__ == "__main__":
    launch_scrcpy_and_agri_erp(click_work_order=True, click_todo_tab=True, open_latest_workorder=True, click_start_job=True, click_user_and_done=True)
