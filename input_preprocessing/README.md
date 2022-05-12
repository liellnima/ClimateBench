# Input Preprocessing Pipeline

## Step 1
Download raw CMIP6 input data and the co2mass from the NorESM-LM model using the provided wget scripts in the **raw_input** folder. You might need to create an ID on the CEDA archive in order to do so. 

## Step 2
Downloaded the unprocessed target data from the NorESM-LM output using the python script 'prepare_data.py'. Attention: it takes a long time to run, best put it on a cluster.

## Step 3
Open the 'prepare_input_data' notebook. Link the directory with the raw CMIP data and the raw target data to the respective path variables. Create a folder to store the preprocessed data into and link it to it's path variable as well. Excetcute every cell in the notebook.
