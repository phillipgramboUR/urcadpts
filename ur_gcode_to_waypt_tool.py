# created by pgra@universal-robots.com
# this file creates a tkinter gui that calls functions to convert a .nc file to a .script file

# imports
import math
import sys
import os
import datetime
from datetime import datetime
import tkinter as tk
from tkinter import *
from tkinter import filedialog

# initialize config info, linked to checkbox input
remove_entry_exit=True # set to false to keep the entry/exit from the Solidworks gcode generator

#######################
# accessory functions #
#######################

# define method for extracting text after a character until the next space
def extract_value(source_string, leading_char):
    tmp_line_partitioned=source_string.partition(leading_char)
    data_after_char=tmp_line_partitioned[2]
    data_after_char_split=data_after_char.split()
    extracted_data=data_after_char_split[0]
    return extracted_data

# define method for converting string list to num list
# ex: '[12,34,56]' to [12,34,56]
def convert_str_list_to_flt_list(str_arg):
    str_list=str_arg.split(",")
    str_x=str_list[0].replace('[','')
    str_y=str_list[1]
    str_z=str_list[2].replace(']','')
    my_num_list=[float(str_x),float(str_y),float(str_z)]
    return my_num_list

# define way to see if points are too close together
dist_thresh=0.05 # in mm
tmp_string_list='[9999999,9999999,9999999]' # initialize a point out of reach of robot
def dist_ok(pt1,pt2):
    x_dist=pt2[0]-pt1[0]
    y_dist=pt2[1]-pt1[1]
    z_dist=pt2[2]-pt1[2]
    dist=math.sqrt(x_dist*x_dist+ y_dist*y_dist+z_dist*z_dist)
    # print('distance between: '+str(pt1)+' and: '+str(pt2)+'is: '+str(dist))
    if (dist>dist_thresh):
        return True
    else:
        return False

####################
# process the file #
####################

def generateOutput():

    # generate name of output file base on input filename
    input_file_name=toolpathfile.partition(".")[0]
    if(checkbox_data_include.get()==True):
        output_file_name=input_file_name+'_points_functions.script' 
    else:
        output_file_name=input_file_name+'_points.script' 

    # get the date and time for putting into the output file header
    try:
        my_timestamp = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
    except:
        my_timestamp = "datetime failed to import"

    # set up number of lines in the incoming file
    i=-1
    def file_len(filename):
        with open(filename) as f:
            for i, _ in enumerate(f):
                pass
        return i + 1
    number_of_lines = file_len(toolpathfile)

    # create an array to work out of
    myData=[]
    with open(toolpathfile,'r') as myFile:
        for line in myFile:
            myData.append(line)

    # set up intermediate data array to write into
    intermediate_data=[]

    # evaluate each line
    for i in range(number_of_lines):
        # get line and work with it
        tmp_line=myData[i]

        # see if this line has coordinates in it
        if (tmp_line[0]=='N')and('X' in tmp_line):
            # extract the parts that come after X, Y, and Z, make it a number list
            x_data=extract_value(tmp_line, 'X')
            y_data=extract_value(tmp_line, 'Y')
            z_data=extract_value(tmp_line, 'Z')
            tmp_num_list=[round(float(x_data),3), round(float(y_data),3),round(float(z_data),3)] 

            # get previous point,  convert it to a num list
            j=len(intermediate_data)
            if(j==0):
                last_pt=tmp_string_list
            else:
                last_pt=intermediate_data[j-1]
            last_pt_num_list=convert_str_list_to_flt_list(last_pt)
        
            # compile line result
            tmp_line_output="["+str(tmp_num_list[0])+", "+str(tmp_num_list[1])+", "+str(tmp_num_list[2])+"]"+","

            # check to see if it is too close to the last point
            if (len(intermediate_data)>1):
                if (dist_ok(tmp_num_list,last_pt_num_list)):
                    intermediate_data.append(tmp_line_output)
            else:
                intermediate_data.append(tmp_line_output)


    # get the data from the checkbox to see if the entry/exits should be removed
    remove_entry_exit=checkbox_data_entryexit.get()

    # check first & last entries to see if they have the same X and Y, and remove them, based on a bool
    if (remove_entry_exit==True):
        # make sure there is enough points for the indexing to work
        if (len(intermediate_data)>2):
            # get first two and last two entries
            lead_in_str=intermediate_data[0]
            first_pt_str=intermediate_data[1]
            final_pt_str=intermediate_data[len(intermediate_data)-2]
            lead_out_str=intermediate_data[len(intermediate_data)-1]

            # compare first two points
            lead_in_nums=convert_str_list_to_flt_list(lead_in_str)
            first_pt_nums=convert_str_list_to_flt_list(first_pt_str)
            if (abs(lead_in_nums[0]-first_pt_nums[0])<dist_thresh)and(abs(lead_in_nums[1]-first_pt_nums[1])<dist_thresh):
                remove_fist_item=True
            else:
                remove_fist_item=False
            
            # compare last two points
            final_pt_nums=convert_str_list_to_flt_list(final_pt_str)
            lead_out_nums=convert_str_list_to_flt_list(lead_out_str)
            if (abs(final_pt_nums[0]-lead_out_nums[0])<dist_thresh)and(abs(final_pt_nums[1]-lead_out_nums[1])<dist_thresh):
                remove_last_item=True
            else:
                remove_last_item=False
            
            # act on evaluation
            if (remove_fist_item==True):
                intermediate_data.pop(0)
            if (remove_last_item==True):
                intermediate_data.pop(len(intermediate_data)-1)                 
            

    # remove last comma
    intermediate_data[len(intermediate_data)-1]=intermediate_data[len(intermediate_data)-1].strip(',')

    # get the source directory, and output filename without the source directory 
    source_directory=os.path.dirname(os.path.abspath(toolpathfile))
    file_split=output_file_name.split('/')
    file_name_only=file_split[len(file_split)-1]
    out_name=file_name_only.partition('.') [0]

    # write to output file    
    with open(os.path.join(source_directory,output_file_name),'a') as my_output_file:
        # empty it out first
        my_output_file.truncate(0)

        # Add header to output file
        my_output_file.write('####################'+'\n')
        my_output_file.write('# generated automatically by a python application'+'\n')
        my_output_file.write('# timestamp: '+my_timestamp+'\n')
        my_output_file.write('# timestamp format: y/m/d/h/m/s' +'\n')
        my_output_file.write('# https://github.com/phillipgramboUR/urcadpts'+'\n')
        my_output_file.write('# pgra@universal-robots.com'+'\n')
        my_output_file.write('####################'+'\n\n')

        # include the utility file
        if(checkbox_data_include.get()==True):
            with open(script_utility) as f:
                for line in f:
                    my_output_file.write(line)
            my_output_file.write('\n\n')

        # mark that this is the start of the data from the toolpath file
        my_output_file.write('###############\n')
        my_output_file.write('# start of information from '+out_name+'\n')
        my_output_file.write('###############\n')

        # write first line
        my_output_file.write('# this is the xyz data from: '+str(input_file_name)+'.nc'+'\n')
        # name the output data set
        matrix_name='urcadpts_data_'+out_name
        my_output_file.write(matrix_name+' = ['+'\n')

        # write data into the file    
        for line in intermediate_data: 
            my_output_file.write(line)
            my_output_file.write("\n")

        # write last line
        my_output_file.write(']'+'\n\n')

        # put the data into variable length URScript lists
        my_output_file.write('# write the fixed sized data set of variable name into variable length lists of static names\n')
        my_output_file.write('# necessary for supporting multiple toolpath sources in a single polyscope program\n')
        my_output_file.write('local num_of_rows = '+matrix_name+'.shape()[0]\n')
        my_output_file.write('local i=0\n')
        my_output_file.write('urcadpts_x_list = make_list(num_of_rows, 0.0, 5000)\n')
        my_output_file.write('urcadpts_y_list = make_list(num_of_rows, 0.0, 5000)\n')
        my_output_file.write('urcadpts_z_list = make_list(num_of_rows, 0.0, 5000)\n')
        my_output_file.write('while i < num_of_rows:\n')
        my_output_file.write('    urcadpts_x_list[i] = '+matrix_name+'[i,0]\n')
        my_output_file.write('    urcadpts_y_list[i] = '+matrix_name+'[i,1]\n')
        my_output_file.write('    urcadpts_z_list[i] = '+matrix_name+'[i,2]\n')
        my_output_file.write('    i = i+1\n')
        my_output_file.write('end\n\n')

        # initialize the counter and length variable
        my_output_file.write('global urcadpts_i = 0\n')
        my_output_file.write('global urcadpts_len = num_of_rows\n\n')


        # mark that this is the end of the data from the toolpath file
        my_output_file.write('###############\n')
        my_output_file.write('# end of information from '+out_name+'\n')
        my_output_file.write('###############\n')
        
        # update final status
        output_status = "Conversion successful!"
        status_label.config(text=output_status)
        # print(output_status)


####################################################################

#######################
# GUI setup/functions #
#######################

# setup variables
log_label_text = "Awaiting File Selection"
toolpathfile = ""
output_status_init="Waiting for Generate Command"
output_status = output_status_init

# Function for opening the file explorer window 
def browseFiles():
    global toolpathfile
    toolpathfile = filedialog.askopenfilename(initialdir="./",
                                                title="Select a Toolpath.nc File",
                                                filetypes=(("Toolpath files","*.nc*"),
                                                           ("all files","*.*")) )

    # Change label contents
    log_label_text = "File Opened: \n" + toolpathfile + "\n"
    label_log.configure(text=log_label_text)
    output_status=output_status_init
    status_label.config(text=output_status)
   
# function for exiting the appliation
def exitNow():
    sys.exit(1)


# the urscript commands to act on the data set in polyscope
# Keep it in the same directory as the application
script_utility='urcadpts_utility.script' 

#################
# build the gui #
#################

# Create the root window
window = tk.Tk()

# Set window title
window.title('UR gcode to waypoints')
# Set window size
window.geometry("350x425")
# Set window background color
window.config(background="white")

# Create a File Explorer label
label_file_explorer = Label(window,
                            text='UR gcode to waypoint tool\n\nSelect toolpath.nc file for conversion\nthen click Generate Report',
                            width=100, height=5,
                            bg="white", fg="black")

button_explore = Button(window,
                        text="Select Toolpath File",
                        command=browseFiles)

button_generate = Button(window,
                         text="Generate Output",
                         command=generateOutput)

button_exit = Button(window,
                     text="Exit",
                     command=exitNow)

checkbox_data_entryexit=BooleanVar()
checkbox_entry_exit=Checkbutton(window, 
                                text='Remove lead in / lead out points? (recommended)',
                                variable=checkbox_data_entryexit)
checkbox_entry_exit.select()

checkbox_data_include=BooleanVar()
checkbox_include=Checkbutton(window,
                            text='Include urcadpts_utility.script?\n Only one file per polyscope program\n can have the function definitions',
                            variable=checkbox_data_include)
checkbox_include.select()

label_log = Label(window,
                  text=log_label_text,
                  #width=100, height=7,
                  bg="white", wraplength=280)

status_label= Label(window,
                  text=output_status,
                  #width=50, height=7,
                  bg="white", wraplength=280)

label_file_explorer.grid(column=1, row=1, pady=(5, 5))

button_explore.grid(column=1, row=2, pady=(5, 5))

button_generate.grid(column=1, row=3, pady=(5, 5))

checkbox_entry_exit.grid(column=1,row=4, pady=(5,5))

checkbox_include.grid(column=1,row=5, pady=(5,5))

button_exit.grid(column=1, row=6, pady=(5, 5))

label_log.grid(column=1, row=7, pady=(5, 5))

status_label.grid(column=1, row=8, pady=(5, 5))

window.grid_columnconfigure(1, weight=1)
# Let the window wait for any events 
window.mainloop()