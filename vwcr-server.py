#!/usr/bin/env python

import SimpleXMLRPCServer
import MySQLdb
import hashlib

__title__ = "VWCR"
__version__ = "0.2"
__author__ = "Koert Loret"

def TestCount(myvar):
    print myvar
    return myvar['name']

def SetReport():
    connection = MySQLdb.connect(host=dbhost,  user=dbuser, passwd=dbpass)
    cursor = connection.cursor()
    selector = "USE " +dbname
    cursor.execute(selector)
    query = "insert into Reports (Paid) values ('1')"
    cursor.execute(query)
    connection.commit()
    cursor.close()
    connection.close()
    return "ok"
    
def GetReport():
    connection = MySQLdb.connect(host=dbhost,  user=dbuser, passwd=dbpass)
    cursor = connection.cursor()
    selector = "USE " +dbname
    cursor.execute(selector)
    
    # Get the latest report date
    query = "Select Time from Reports where Paid = 1 order by Time Desc"
    cursor.execute(query)
    fetched = cursor.fetchone()
    lastreport = fetched[0]
    
    # Get Drinks
    query = "select * from BarLog where Time > '" + str(lastreport) + "'"
    cursor.execute(query)
    DrinksList = cursor.fetchall()
    
    #Get DrinkInfo
    Result = []
    for Entry in DrinksList:
        query = "Select * from Bar where ID = " + str(Entry[1])
        cursor.execute(query)
        Item = cursor.fetchone()
        Drink = []
        Drink.append(Entry[2])
        Drink.append(Item[0])
        Drink.append(Item[1])
        Drink.append(Item[2])
        Drink.append(Item[3])
        Drink.append(Item[4])
        Drink.append(Item[5])
        Drink.append(Item[6])
        Drink.append(Item[7])
        Result.append(Drink)
    cursor.close()
    connection.close()
    answer = []
    return Result
    
def SellDrink(Drink, User):
    connection = MySQLdb.connect(host=dbhost,  user=dbuser, passwd=dbpass)
    cursor = connection.cursor()
    selector = "USE " +dbname
    cursor.execute(selector)
    
    # get current stock
    query = "select Stock from Bar where ID = " + str(Drink['id'])
    cursor.execute(query)
    currentstock = cursor.fetchone()
    
    # calculate new stock
    newstock =  int(currentstock[0]) - 1
    
    # set new stock
    query = "update Bar set Stock = %s where ID = %s"
    cursor.execute(query, (newstock, Drink['id']))
    connection.commit()

    # get UserID
    BuyerID = "Error"
    FirstName = User[0]
    LastName = User[1]
    if FirstName == "Cash":
        BuyerID = "Cash"
    else:
        query = "select ID from Users where Firstname = %s and LastName = %s"
        cursor.execute(query, (FirstName, LastName))
        currentbuyer = cursor.fetchone()
        BuyerID = currentbuyer[0]
        # DeductCost
        query = "select Account from Users where ID = " + str(BuyerID)
        cursor.execute(query)
        CurrentAccount = cursor.fetchone()[0]
        NewAccount = float(CurrentAccount) - float(Drink['price'])
        query ="update Users set Account = %s where ID = %s"
        cursor.execute(query,  (NewAccount,  BuyerID))
        connection.commit()
        
    # add to log
    query = "insert into BarLog (DrinkID, UserID) values (%s, %s)"
    cursor.execute(query,  (Drink['id'],  BuyerID))
    
    cursor.close()
    connection.commit()
    connection.close()
    return "done"
    
def GetStockList():
    connection = MySQLdb.connect(host=dbhost,  user=dbuser, passwd=dbpass)
    cursor = connection.cursor()
    selector = "USE " +dbname
    cursor.execute(selector)
    cursor.execute("SELECT * from Bar order by Type, Name")
    rows = cursor.fetchall()
    return rows
    cursor.close()

def GetUserList():
    connection = MySQLdb.connect(host=dbhost,  user=dbuser, passwd=dbpass)
    cursor = connection.cursor()
    selector = "USE " +dbname
    cursor.execute(selector)
    cursor.execute("SELECT FirstName, LastName from Users where ActiveMember = 1 order by FirstName, LastName")
    rows = cursor.fetchall()
    return rows

def VerifyBuyer(firstname, lastname,  price,  password):
    hash = hashlib.md5(password).hexdigest()
    connection = MySQLdb.connect(host=dbhost,  user=dbuser, passwd=dbpass)
    cursor = connection.cursor()
    selector = "USE " +dbname
    cursor.execute(selector)
    query = "SELECT * From Users where Firstname = '" + firstname + "' and LastName = '" + lastname + "' and Account >= " + str(price) + " and Password = '" + hash + "'"
    cursor.execute(query)
    rows = cursor.fetchall()
    return len(rows)
    
# Database
dbhost = "localhost"
dbname = "malman"
dbuser = "malman"
dbpass = ""
dbport = "3306"

# VWCR_Server
adres = ("0.0.0.0",  9000)
server = SimpleXMLRPCServer.SimpleXMLRPCServer(adres)
server.register_function(TestCount)
server.register_function(GetStockList)
server.register_function(SellDrink)
server.register_function(GetReport)
server.register_function(SetReport)
server.register_function(GetUserList)
server.register_function(VerifyBuyer)
server.register_introspection_functions()
server.serve_forever()
