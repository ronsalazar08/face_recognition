
#!/usr/bin/python3

import pymysql

# Open database connection
db = pymysql.connect("10.44.2.161","remote","1111","TorresTech" )

# prepare a cursor object using cursor() method
cursor = db.cursor()
file_name = 160913
# Prepare SQL query to INSERT a record into the database.
sql = f"SELECT firstname, middlename, lastname, company, shift FROM contractor_employee WHERE face_id = {file_name}"

# Execute the SQL command
cursor.execute(sql)

# Fetch all the rows in a list of lists.
results = cursor.fetchall()
for row in results:
   fname = row[0]
   mname = row[1]
   lname = row[2]
   company = row[3]
   shift = row[4]
   # Now print fetched result
   print (fname, mname, lname, company, shift )

# disconnect from server
db.close()
