import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
from streamlit_option_menu import option_menu

# API configuration
API_BASE_URL = "http://localhost:8501/api"

def init_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.is_admin = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.session_state.session_token = None

def handle_login(username: str, password: str) -> bool:
    response = requests.post(
        f"{API_BASE_URL}/login",
        json={"username": username, "password": password}
    )
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            user = data['user']
            st.session_state.logged_in = True
            st.session_state.is_admin = user['is_admin']
            st.session_state.username = user['username']
            st.session_state.user_id = user['id']
            st.session_state.session_token = user['session_token']
            return True
    return False

def display_login():
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if handle_login(username, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials or account not approved")

def display_user_registration():
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Register")

        if submit:
            response = requests.post(
                f"{API_BASE_URL}/register",
                json={
                    "username": username,
                    "email": email,
                    "password": password,
                    "confirm_password": confirm_password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    st.success("Registration successful! Please wait for admin approval.")
                else:
                    st.error(data['error'])
            else:
                st.error("Registration failed. Please try again.")

def main():
    st.set_page_config(page_title="CXL-QVP Login", layout="wide")
    init_session_state()

    if not st.session_state.logged_in:
        with st.sidebar:        
            page = option_menu(
                menu_title='CXL-QVP',
                options=['Login', 'Register', 'About'],
                icons=['person-circle', 'person-plus','info-circle'],
                menu_icon='cast',
                default_index=0,
                styles={
                    "container": {"padding": "0!important","background-color":'white'},
                    "icon": {"color": "black", "font-size": "23px"}, 
                }
            )
    else:
        if st.session_state.is_admin:
            with st.sidebar:                    
                page = option_menu(
                    menu_title='CXL-QVP',
                    options=['Home','Users', 'Agents', 'Audit Logs', "Logout"],
                    icons=['house','people-fill', 'hdd-stack-fill','card-text', 'door-closed'],
                    menu_icon='cast',
                    default_index=0,
                    styles={
                        "container": {"padding": "0!important","background-color":'white'},
                        "icon": {"color": "black", "font-size": "23px"}, 
                    }
                )
        else:
            with st.sidebar:        
                page = option_menu(
                    menu_title='CXL-QVP',
                    options=['User Dashboard','Logout'],
                    icons=['house','door-closed'],
                    menu_icon='cast',
                    default_index=0,
                    styles={
                        "container": {"padding": "0!important","background-color":'white'},
                        "icon": {"color": "black", "font-size": "23px"}, 
                    }
                )            

    if page == "Login":
        st.title("Login")
        display_login()

    elif page == "Register":
        st.title("Register")
        display_user_registration()

    elif page == "Home" and st.session_state.is_admin:
        st.title("Admin Dashboard")
        st.write(f"Welcome, {st.session_state.username}!")
        display_pending_approvals()

    elif page == "Agents":
        display_server_resources()

    elif page == "Users" and st.session_state.is_admin:
        display_manage_users()

    elif page == "Audit Logs" and st.session_state.is_admin:
        display_audit_logs()

    elif page == "User Dashboard" and st.session_state.logged_in:
        st.title("User Dashboard")
        st.write(f"Welcome, {st.session_state.username}!")
        response = requests.get(
            f"{API_BASE_URL}/users/{st.session_state.user_id}",
            headers={"Authorization": st.session_state.session_token}
        )
        
        if response.status_code == 200:
            user = response.json()
            if user['redirect_url']:
                st.write("You will be redirected to your assigned application.")
                url = (
                    user['redirect_url']
                    + f"?user={st.session_state.username}&session_token={st.session_state.session_token}"
                )
                st.write(f"Assigned URL: {url}")
            else:
                st.warning("No redirect URL has been assigned to your account yet.")

    elif page == "Logout":
        response = requests.post(
            f"{API_BASE_URL}/logout",
            json={"user_id": st.session_state.user_id},
            headers={"Authorization": st.session_state.session_token}
        )
        
        if response.status_code == 200:
            st.session_state.logged_in = False
            st.session_state.is_admin = False
            st.session_state.username = None
            st.session_state.user_id = None
            st.session_state.session_token = None
            st.success("Logged out successfully!")
            st.rerun()

    elif page == "About":
        st.markdown('CXL-QVP Self-Hosted Cloud Development Environment')
        st.markdown('Created by: [QVP Team](Using AI)')

def display_pending_approvals():
    response = requests.get(
        f"{API_BASE_URL}/users/pending",
        headers={"Authorization": st.session_state.session_token}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            users = data['users']
            if users:
                df = pd.DataFrame(users)
                df = df.rename(columns={
                    "username": "Username",
                    "email": "Email",
                    "created_at": "Registration Date"
                })
                df["Registration Date"] = pd.to_datetime(df["Registration Date"]).dt.strftime("%Y-%m-%d %H:%M:%S")
                
                st.write(f"Found {len(df)} pending approval(s)")
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Approval form
                selected_user = st.selectbox(
                    "Select user to approve",
                    options=df["Username"].tolist(),
                    key="user_to_approve"
                )
                
                if selected_user:
                    user_id = df[df["Username"] == selected_user]["id"].values[0]
                    server_response = requests.get(
                        f"{API_BASE_URL}/server-resources",
                        headers={"Authorization": st.session_state.session_token}
                    )
                    
                    if server_response.status_code == 200:
                        server_data = server_response.json()
                        if server_data['success']:
                            servers = [s['server_id'] for s in server_data['servers']]
                            selected_server = st.selectbox(
                                "Select a server for the user",
                                options=servers,
                                key=f"server_select_{user_id}"
                            )
                            
                            if st.button("Approve User"):
                                approve_response = requests.post(
                                    f"{API_BASE_URL}/users/{user_id}/approve",
                                    json={"server_id": selected_server},
                                    headers={"Authorization": st.session_state.session_token}
                                )
                                
                                if approve_response.status_code == 200:
                                    st.success(f"Approved user {selected_user} and assigned to server {selected_server}")
                                    st.rerun()
                        else:
                            st.error("No servers available for assignment")
            else:
                st.info("No pending approvals")
        else:
            st.error(data['error'])

def display_manage_users():
    response = requests.get(
        f"{API_BASE_URL}/users",
        headers={"Authorization": st.session_state.session_token}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            users = data['users']
            if users:
                df = pd.DataFrame(users)
                df = df.rename(columns={
                    "id": "ID",
                    "username": "Username",
                    "email": "Email",
                    "is_approved": "Approved",
                    "redirect_url": "Redirect URL",
                    "created_at": "Created At"
                })
                df["Approved"] = df["Approved"].apply(lambda x: "Yes" if x else "No")
                df["Created At"] = pd.to_datetime(df["Created At"]).dt.strftime("%Y-%m-%d %H:%M:%S")
                
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Delete user section
                selected_user = st.selectbox(
                    "Select a user to delete",
                    options=df["Username"].tolist(),
                    key="delete_user_selectbox"
                )
                
                if selected_user:
                    user_id = df[df["Username"] == selected_user]["ID"].values[0]
                    if st.button("Delete User"):
                        delete_response = requests.delete(
                            f"{API_BASE_URL}/users/{user_id}",
                            headers={"Authorization": st.session_state.session_token}
                        )
                        
                        if delete_response.status_code == 200:
                            st.success(f"User '{selected_user}' has been deleted.")
                            st.rerun()
            else:
                st.info("No users found in the database.")
        else:
            st.error(data['error'])

def display_audit_logs():
    st.subheader("Audit Logs")
    
    # Get all users for the filter
    users_response = requests.get(
        f"{API_BASE_URL}/users",
        headers={"Authorization": st.session_state.session_token}
    )
    
    if users_response.status_code == 200:
        users_data = users_response.json()
        if users_data['success']:
            user_options = ["All Users"] + [user["username"] for user in users_data['users']]
            
            col1, col2 = st.columns(2)
            
            with col1:
                user_filter = st.selectbox(
                    "Filter by User",
                    options=user_options,
                    key="audit_user_filter"
                )
            
            with col2:
                n_rows = st.select_slider(
                    "Number of rows",
                    options=[10, 25, 50, 100, 500],
                    value=100,
                    key="n_rows_slider",
                )
            
            try:
                response = requests.get(
                    f"{API_BASE_URL}/audit-logs",
                    headers={"Authorization": st.session_state.session_token},
                    params={
                        "username": user_filter if user_filter != "All Users" else None,
                        "limit": n_rows
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data['success']:
                        logs = data['logs']
                        if logs:
                            # Process the logs to ensure proper format
                            processed_logs = []
                            for log in logs:
                                processed_log = {
                                    "Timestamp": pd.to_datetime(log["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
                                    "Username": log["username"],
                                    "Action": log["action_type"],
                                    "IP Address": log["ip_address"],
                                    "Details": str(log.get("action_details", {}))
                                }
                                processed_logs.append(processed_log)
                            
                            # Create DataFrame
                            df = pd.DataFrame(processed_logs)
                            
                            # Add search functionality
                            search_term = st.text_input("Search in logs:", "")
                            if search_term:
                                mask = (
                                    df.astype(str)
                                    .apply(lambda x: x.str.contains(search_term, case=False))
                                    .any(axis=1)
                                )
                                df = df[mask]
                            
                            # Display data info
                            st.write(f"Showing {len(df)} records")
                            
                            # Display the DataFrame with sorting enabled
                            st.dataframe(
                                df,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "Timestamp": st.column_config.TextColumn(
                                        "Timestamp",
                                        width="medium",
                                    ),
                                    "Username": st.column_config.TextColumn(
                                        "Username",
                                        width="small",
                                    ),
                                    "Action": st.column_config.TextColumn(
                                        "Action",
                                        width="small",
                                    ),
                                    "IP Address": st.column_config.TextColumn(
                                        "IP Address",
                                        width="small",
                                    ),
                                    "Details": st.column_config.TextColumn(
                                        "Details",
                                        width="large",
                                    ),
                                },
                            )
                            
                            # Add export functionality
                            if st.button("Export to CSV"):
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    label="Download CSV",
                                    data=csv,
                                    file_name="audit_logs.csv",
                                    mime="text/csv",
                                )
                            
                        else:
                            st.info("No audit logs found")
                    else:
                        st.error(data['error'])
                else:
                    st.error("Failed to fetch audit logs")
            except Exception as e:
                st.error(f"Error retrieving audit logs: {str(e)}")
                st.info("If this is a new installation, make sure the audit_log table is properly created.")
        else:
            st.error("Failed to fetch users for filter")
    else:
        st.error("Failed to fetch users for filter")

def display_server_resources():
    response = requests.get(
        f"{API_BASE_URL}/server-resources",
        headers={"Authorization": st.session_state.session_token}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            servers = data['servers']
            if servers:
                df = pd.DataFrame(servers)
                df = df.rename(columns={
                    "cpu_count": "CPU Cores",
                    "total_memory": "Total Memory (GB)",
                    "host_cpu_used": "Host CPU Used (%)",
                    "host_memory_used": "Host Memory Used (GB)",
                    "docker_instances": "Docker Instances",
                    "allocated_cpu": "Allocated CPU (Cores)",
                    "allocated_memory": "Allocated Memory (GB)",
                    "remaining_cpu": "Remaining CPU (Cores)",
                    "remaining_memory": "Remaining Memory (GB)",
                })
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No servers available.")
        else:
            st.error(data['error'])

if __name__ == "__main__":
    main()