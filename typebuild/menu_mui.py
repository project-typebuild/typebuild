from streamlit_elements import elements, mui, html, sync
import streamlit as st

# set Streamlit page layout to wide
def display_menu_bar(menu_options):
    if 'activeStep' not in st.session_state:
        st.session_state.activeStep = 0
    # Create functions dynamically to handle Button clicks
    for i in range(len(menu_options)):
        # Create the function if it doesn't exist in locals

        if f"menu_button_function_{i}" not in locals():
            myfunc = f"""def menu_button_function_{i}(event):
                st.sidebar.warning(f"Button {menu_options[i]} clicked")
                st.session_state.activeStep = {i}
                st.session_state.show_dropdown = True
                return None
            """            
            exec(myfunc)

    with elements("App Bar"):
        with mui.AppBar(position="relative", sx = {'borderRadius': 10}):
            with mui.Toolbar(disableGutters=True, variant="dense"):
                for i, b in enumerate(menu_options):
                    with mui.Grid(container=True, spacing=0):
                        mui.Button(color="inherit", onClick= eval(f'menu_button_function_{i}'))(b.split('~')[0])


display_menu_bar(['Home~home', 'Users~users', 'Projects~projects', 'Settings~settings'])