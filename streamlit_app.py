# Import Python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas as pd

# Title and instructions
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Smoothie name input
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Snowflake connection
cnx = st.connection("snowflake")
session = cnx.session()

# Fetch fruit data from Snowflake
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))

# Convert Snowpark dataframe to Pandas dataframe
pd_df = my_dataframe.to_pandas()

# Multi-select for ingredients
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    pd_df['FRUIT_NAME'].tolist(),  # Show only fruit names
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        # Get SEARCH_ON value for the selected fruit
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        
        # Show subheader for nutrition info
        st.subheader(f"{fruit_chosen} Nutrition Information")
        api_url = f"https://smoothiefroot.com/api/fruit/{search_on.lower()}"
        st.write("Generated URL:", api_url)



        try:
            smoothiefroot_response = requests.get(api_url, timeout=7)
            smoothiefroot_response.raise_for_status()  # Raise error if request fails

            # Convert JSON response to Pandas DataFrame
            fv_df = pd.DataFrame(smoothiefroot_response.json())

            # Display in Streamlit
            st.dataframe(data=fv_df, use_container_width=True)

        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {e}")

    # Insert into Snowflake
    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders(ingredients, name_on_order)
        VALUES ('{ingredients_string}', '{name_on_order}')
    """

    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success('Your Smoothie is ordered!', icon="✅")

# Example static API call for testing
st.write("### Test API Call Example")
try:
    test_response = requests.get("https://smoothiefroot.com/api/fruit/watermelon")
    test_response.raise_for_status()
    st.dataframe(data=pd.DataFrame(test_response.json()), use_container_width=True)
except requests.exceptions.RequestException as e:
    st.error(f"Test API call failed: {e}")
