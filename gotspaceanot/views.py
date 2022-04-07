from django.shortcuts import render, redirect
from django.db import connection
from django.shortcuts import render
from django.http import HttpResponse
from collections import OrderedDict

# Create your views here.
def administrator(request):
    ## Delete student
    if request.POST:
        if request.POST['action'] == 'delete':
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM student WHERE matric_number = %s", [request.POST['Matric Number']])    
                cursor.execute("DELETE FROM library_system WHERE matric_number = %s", [request.POST['Matric Number']])    
                
                
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM student ORDER BY library")
        student = cursor.fetchall()   
        
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM library_system ORDER BY library")
        library_system = cursor.fetchall()    
        
    result_dict = {'library_system': library_system, 'student':student }
    
    return render(request, 'gotspaceanot/administrator.html',result_dict)

def welcome(request): 
    """Shows the main page"""    
    ## Use raw query to get all objects
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM available ORDER BY library")
        available = cursor.fetchall()
        
    with connection.cursor() as cursor:
        cursor.execute("SELECT library, SUM(available_seats) as Total_Available_Seats, SUM(total_seats) as Total_Space FROM available GROUP BY library ORDER BY library ASC")
        total_space_available = cursor.fetchall()
        
    result_dict = {'records': available, 'records_total': total_space_available}    
    
    return render(request, 'gotspaceanot/welcome.html', result_dict)


def library_system_records(request):
    """Shows the main page"""    
    
    ## Use raw query to get all objects
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM library_system ORDER BY library")
        library_system = cursor.fetchall()
        
    result_dict_2 = {'records_library': library_system}    

    return render(request, "gotspaceanot/library_system_records.html", result_dict_2)

def nus_system(request):
    """Shows the main page"""    
    
    ## Use raw query to get all objects
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM nus_system")
        nus_system = cursor.fetchall()
        
    result_dict_2 = {'records_nus': nus_system}    

    return render(request, "gotspaceanot/nus_system.html", result_dict_2)

def about(request):
    return render(request, 'gotspaceanot/about.html')

def login(request):
    """Shows the main page"""
    context = {}
    status = ''

    if request.POST:
        ## Check if martic_number is already in the table
        with connection.cursor() as cursor:     

            #Getting all the required table rows.
            cursor.execute("SELECT * FROM library_system WHERE matric_number = %s", [request.POST['Matric Number']])
            library = cursor.fetchone()
            cursor.execute("SELECT * FROM NUS_system WHERE matric_number = %s", [request.POST['Matric Number']])
            nus_system = cursor.fetchone()
            cursor.execute("SELECT * FROM student WHERE matric_number = %s", [request.POST['Matric Number']])
            student = cursor.fetchone()
            
            #To catch the error when the student have not tapped into the library but wants to login in as if he is at the seat already.
            #This prevents seats booking in advance as well.
            if library == None:
                status = 'Please tap into the library first before logging in or check if your matric is the same as registered.'
                context['status'] = status                
                return render(request, "gotspaceanot/login.html", context)
            
            #To catch the error when the student inputs the wrong library: E.g. He tapped into CLB but inputted SLB          
            if library[1] != request.POST['Library']:
                status = 'Please choose the correct library,%s first to log in.' % (library[1])
                context['status'] = status
                return render(request, "gotspaceanot/login.html", context)

            

            #To catch the error when the student input a wrong matric number or has not registered matric number
            if nus_system[0] != request.POST['Matric Number']:
                status = 'Matric Number %s has not registered yet or is not the same as registered matric' % (request.POST['Matric Number'])
                context['status'] = status
                return render(request, "gotspaceanot/login.html", context)
            
            if nus_system[1] != request.POST['Email']:
                status = 'Email %s has not registered yet or is not the same as registered email' % (request.POST['Email'])
                context['status'] = status
                return render(request, "gotspaceanot/login.html", context)
            

            ## No student with same matric card
            if student == None:
                ##TODO: date validation
                cursor.execute("INSERT INTO student VALUES (%s, %s, %s, %s)"
                        , [request.POST['Matric Number'], request.POST['Email'], request.POST['Library'], request.POST['Level']])
                ##Updating the available space when a student register which level he is going to study 
                cursor.execute("UPDATE available SET available_seats = available_seats - 1 WHERE (library,level) =  (%s, %s)", [request.POST['Library'],request.POST['Level']] )
                return redirect('gotspaceanot-logout') 
            else:
                status = 'Student with Matric Number %s already exists' % (request.POST['Matric Number'])
                


    context['status'] = status
 
    return render(request, "gotspaceanot/login.html", context)

def register(request):
    """Shows the main page"""
    context = {}
    status = ''

    if request.POST:
        ## Check if student is already in the table
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM NUS_system WHERE matric_number = %s", [request.POST['Matric Number']])
            student = cursor.fetchone()
            ## No student with same matric card
            if student == None:
                ##TODO: date validation
                cursor.execute("INSERT INTO NUS_system VALUES (%s, %s, %s, %s,%s)"
                        , [request.POST['Matric Number'], request.POST['Email'], request.POST['Department'], request.POST['Year'],request.POST['Stay']])
                ##Updating the NUS_system when a student register for the app
                return redirect('gotspaceanot-login') 
            else:
                status = 'Student with Matric Number %s already registered' % (request.POST['Matric Number'])


    context['status'] = status
 
    return render(request, "gotspaceanot/register.html", context)

def logout(request):
    """Shows the main page"""
    context = {}
    status = ''

    if request.POST:
        ## Check if matric_number is already in the table
        with connection.cursor() as cursor:

            cursor.execute("SELECT * FROM student WHERE matric_number = %s", [request.POST['Matric Number']])
            stu = cursor.fetchone()
            ## No student with same matric card
            if stu == None:
                status = 'Student with Matric Number %s does not exists' % (request.POST['Matric Number'])
            else:
                ##Updating the available space when a student logs out
                cursor.execute("UPDATE available SET available_seats = available_seats + 1 WHERE (library,Level) = (%s, %s)", [stu[2] , stu[3]])
                cursor.execute("DELETE FROM student WHERE matric_number = %s", [request.POST['Matric Number']])
                cursor.execute("DELETE FROM library_system WHERE matric_number = %s", [request.POST['Matric Number']])

                return redirect('gotspaceanot-welcome') 

    context['status'] = status
 
    return render(request, "gotspaceanot/logout.html", context)

def library_system(request):
    context = {}
    status = ''

    if request.POST:
        ## Check if customerid is already in the table
        with connection.cursor() as cursor:

            cursor.execute("SELECT * FROM library_system WHERE matric_number = %s", [request.POST['Matric Number']])
            library_system = cursor.fetchone()
            ## No student with same id
                
            if library_system == None:
                ##TODO: date validation
                cursor.execute("INSERT INTO library_system VALUES (%s, %s)"
                        , [request.POST['Matric Number'], request.POST['Library'] ])
                return redirect('gotspaceanot-welcome')    
            else:
                status = 'Student with Matric Number %s already inside the library' % (request.POST['Matric Number'])

    context['status'] = status
 
    return render(request, "gotspaceanot/library_system.html", context)   

def edit(request, id):
    """Shows the main page"""

    # dictionary for initial data with
    # field names as keys
    context ={}

    # fetch the object related to passed id
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM student  WHERE matric_number = %s", [id])
        obj = cursor.fetchone()

    status = ''
    # save the data from the form

    if request.POST:
        ##TODO: date validation
        with connection.cursor() as cursor:           
            cursor.execute("UPDATE student SET matric_number = %s, email = %s, library = %s, Level = %s WHERE matric_number = %s"
                    , [request.POST['matric_number'], request.POST['email'], request.POST['library'],
                        request.POST['Level'] , id ])   
            cursor.execute("UPDATE available SET available_seats = available_seats + 1 WHERE (library,level) =  (%s, %s)", [obj[2],obj[3]] )
            cursor.execute("UPDATE available SET available_seats = available_seats - 1 WHERE (library,level) =  (%s, %s)", [request.POST['library'],request.POST['Level']] )
            status = 'Student details edited successfully!'
            cursor.execute("SELECT * FROM student WHERE matric_number = %s", [id])
            obj = cursor.fetchone()


    context["obj"] = obj
    context["status"] = status
 
    return render(request, "gotspaceanot/edit.html", context)

def filter(request):
    """Shows the main page"""
    #To find students who stay on campus and the total number
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM student WHERE matric_number IN(SELECT matric_number FROM NUS_system WHERE hall = '1')")
        stay_in = cursor.fetchall()
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM student WHERE matric_number IN(SELECT matric_number FROM NUS_system WHERE hall = '1')")
        stay_in_total = cursor.fetchall()
    #To find students who stay off campus and the total number
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM student WHERE matric_number IN(SELECT matric_number FROM NUS_system WHERE hall = '0')")
        stay_out = cursor.fetchall()
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM student WHERE matric_number IN(SELECT matric_number FROM NUS_system WHERE hall = '0')")
        stay_out_total = cursor.fetchall()
        
    with connection.cursor() as cursor:
	    cursor.execute("SELECT student_department,COUNT(student_department) FROM NUS_system WHERE matric_number IN (SELECT matric_number FROM student) GROUP BY student_department")
	    department_total = cursor.fetchall()    
	
    with connection.cursor() as cursor:
	    cursor.execute("SELECT faculty, COUNT(faculty) FROM department where department IN (SELECT student_department FROM NUS_system WHERE matric_number IN (SELECT matric_number FROM student) GROUP BY student_department) GROUP BY faculty")
	    faculty_total = cursor.fetchall() 
        
    result_dict3 = {'stay_in':stay_in,'stay_in_total':stay_in_total,'stay_out':stay_out,'stay_out_total':stay_out_total,'department_total':department_total, 'faculty_total':faculty_total}

    return render(request, "gotspaceanot/filter.html",result_dict3)



# Include the `fusioncharts.py` file that contains functions to embed the charts.
from ..fusioncharts import FusionCharts

# Loading Data from a Ordered Dictionary
# Example to create a column 2D chart with the chart data passed as Dictionary format.
# The `chart` method is defined to load chart data from Dictionary.
def chart(request):

    with connection.cursor() as cursor:
	    cursor.execute("SELECT faculty, COUNT(faculty) FROM department where department IN (SELECT student_department FROM NUS_system WHERE matric_number IN (SELECT matric_number FROM student) GROUP BY student_department) GROUP BY faculty")
	    faculty_total = cursor.fetchall() 
	
    # Chart data is passed to the `dataSource` parameter, as dictionary in the form of key-value pairs.
    dataSource = OrderedDict()

    # The `chartConfig` dict contains key-value pairs data for chart attribute
    chartConfig = OrderedDict()
    chartConfig["caption"] = "Faculties of students who visit the libraries"
    chartConfig["xAxisName"] = "Faculty"
    chartConfig["yAxisName"] = "Number"
    chartConfig["theme"] = "fusion"

    # The `chartData` dict contains key-value pairs data
    chartData = OrderedDict()
    chartData[faculty_total[0][0]] = faculty_total[0][1]


    dataSource["chart"] = chartConfig
    dataSource["data"] = []

    # Convert the data in the `chartData` array into a format that can be consumed by FusionCharts.
    # The data for the chart should be in an array wherein each element of the array is a JSON object
    # having the `label` and `value` as keys.

    # Iterate through the data in `chartData` and insert in to the `dataSource['data']` list.
    for key, value in chartData.items():
        data = {}
        data["label"] = key
        data["value"] = value
        dataSource["data"].append(data)


    # Create an object for the column 2D chart using the FusionCharts class constructor
    # The chart data is passed to the `dataSource` parameter.
    column2D = FusionCharts("column2d", "ex1" , "600", "400", "chart-1", "json", dataSource)

    return  render(request, "gotspaceanot/charts.html",{'output' : column2D.render(), 'chartTitle': 'Simple Chart Using Array'})

