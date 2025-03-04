import pandas as pd
import os
import time
from datetime import datetime

from time import mktime
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import style
style.use('dark_background')
import re

#file path to data, include the r in front to make sure python does not read teh \'s as escape characters

path = r"C:\Users\22cmc\Downloads\intraQuarter\intraQuarter"

#fucntion to target the total equity info within the Keystats file
def key_stats(gather = "Total Debt/Equity (mrq)"):
    statspath = path+'/_KeyStats'
    stock_list = [x[0] for x in os.walk(statspath)]
    #print(stock_list)
    df_data = [] #Creating epty list for all the data we will be using

    ticker_list = [] #creating epty list for the tickers

    #Creating dataframe with sp500 data
    sp500_df = pd.read_csv("SPX.csv")
    #print(sp500_df)

    for each_dir in stock_list[1:]: #looks at each directory within the above stock list except the first element, because that is just the current directory
        each_file = os.listdir(each_dir) #looking at the files in each directory
        ticker = os.path.basename(each_dir) #returns final component of a given path, usually returns the name of given file or directory, in this case, its the companys ticker
        ticker_list.append(ticker) #keeping track of all the tickers

        starting_stock_value = False #keeping track of whether or not we are moving onto a new stock or not
        starting_sp500_value = False



        if len(each_file) > 0: #making sure the file is not empty
            for file in each_file:
                try:
                    date_stamp = datetime.strptime(file, '%Y%m%d%H%M%S.html') #creating the ime stamp, based on the name of the file year,month,day,hour,minute,second
                    #print(date_stamp)
                    unix_time = time.mktime(date_stamp.timetuple())
                    #print(date_stamp, unix_time)
                except ValueError as  ve:
                    pass
                    

                full_path_to_file = each_dir+'/'+file #creating path to full html file to look for specific data and corresponging values
                source = open(full_path_to_file,'r').read()
                #print(source)



                try:
                    # Attempt to get the debt/equity value from the source
                    raw_value = source.split(gather + ':</td><td class="yfnc_tabledata1">')[1].split('</td>')[0]
                    d_e_value = 'N/A' if raw_value == "N/A" else float(raw_value)
                except (IndexError, ValueError) as e:  # Handles missing data specifically
                    #print(e, ticker, file)
                    try:
                        # Secondary attempt if previous method fails
                        raw_value = source.split(gather + ':</th><td class="yfnc_tabledata1">')[1].split('</td>')[0]
                        d_e_value = 'N/A' if raw_value == "N/A" else float(raw_value)
                    except (IndexError, ValueError):
                        d_e_value = 'N/A'  # Final fallback if all parsing fails
                    
                

                try:
                    # Initial attempt to extract stock price
                    stock_price = float(source.split('</small><big><b>')[1].split('</b></big>')[0])
                except (IndexError, ValueError) as e:
                    #print('First parsing failed:', e)
                    try:
                        #print('Testing secondary parsing')
                        # Attempt regex parsing
                        stock_price_text = source.split('</small><big><b>')[1].split('</b></big>')[0]
                        stock_price_match = re.search(r'(\d{1,8}\.\d{1,8})', stock_price_text)
                        if stock_price_match:
                            stock_price = float(stock_price_match.group(1))
                            #print('Passed secondary parsing')
                        else:
                            pass
                            #raise ValueError("Stock price pattern not found in secondary parsing")
                    except (IndexError, ValueError) as e:
                        #print('Entering tertiary parsing:', e)
                        try:
                            # Final attempt if previous methods fail
                            stock_price_text = source.split('<span class="time_rtq_ticker">')[1].split('</span>')[0]
                            stock_price_match = re.search(r'(\d{1,8}\.\d{1,8})', stock_price_text)
                            if stock_price_match:
                                stock_price = float(stock_price_match.group(1))
                                #print("Passed tertiary parsing")
                            else:
                                pass
                                #raise ValueError("Stock price pattern not found in tertiary parsing")
                        except (IndexError, ValueError) as e:
                            #print("Failed to extract stock price:", e)
                            stock_price = None  # Assign a fallback value or handle error accordingly

                    #except Exception as e:
                        #print(e, ticker, file)
                        #d_e_value = 'N/A' #if the debt/equity isnt there, usually we get a index error, so we just set the value to 'N/A' so we can use a if statement later to prevent it from going into the dataframe, as it wont be helpful
                        #stock_price = None #usually the value error, so just changing it to none , so we can skip it later on if needed

                if stock_price is not None:
                    if not starting_stock_value:
                        starting_stock_value = stock_price #keeping track of starting value to see change

                    
                    try:
                        sp500_date = datetime.fromtimestamp(unix_time).strftime('%Y-%m-%d') #getting the sp500 time stamp to see if it matches the company data dates

                        row = sp500_df[sp500_df["Date"] == sp500_date] #getting the row for the specified day
                        
                        sp500_value = float(row["Adj Close"].iloc[0]) #Getting the closing value for the day

                        if not starting_sp500_value:# checking to see if we moved to a new stock or not
                            starting_sp500_value = sp500_value

                        stock_p_change = ((stock_price - starting_stock_value) / starting_stock_value) * 100 #finding the percent change of the specified stock for the day
                        sp500_p_change = ((sp500_value - starting_sp500_value) / starting_sp500_value) * 100 #finding the percent change for the sp500 for the day
                        
                    except Exception as e: #handling errors that may occur, usually with missing or incorrect data in the stock files
                        sp500_value = None 
                        stock_p_change = None #may occur if there is a calculation error for some reason. Will convert to o when adding it to the df
                        sp500_p_change = None

                    difference = stock_p_change - sp500_p_change if stock_p_change is not None and sp500_p_change is not None else 0

                    if difference > 0:
                        status = "outperform"
                    else:
                        status = "underperform"


                if d_e_value != 'N/A': # as long as the value is valid, and not corrupted in some way then add it to our data frame list
                    df_data.append({
                        'Date': date_stamp,
                        'Unix': unix_time,
                        'Ticker': ticker,
                        'Debt Equity Ratio': d_e_value,
                        'Price':stock_price,
                        'stock_p_change': stock_p_change if stock_p_change is not None else 0, # if the value is none change it to 0 just to have a number there
                        'sp500':sp500_value,
                        'sp500_p_change': sp500_p_change if sp500_p_change is not None else 0,
                        'difference': difference,
                        'status': status
                        })#appending the data to the list under its correct name. this is using a dictionary

    #turning the data frame list into an actual data frame using pandas
    df = pd.DataFrame(df_data, columns=[
        "Date",
        "Unix",
        "Ticker",
        "Debt Equity Ratio",
        "Price",
        "stock_p_change",
        "sp500",
        "sp500_p_change",
        "difference",
        "status"]) #creating a pandas dataframe with all the data stored in the array above.

            
    """
    for each_ticker in ticker_list:
        try:
            plot_df = df[(df['Ticker'] == each_ticker)]
            plot_df = plot_df.set_index(['Date'])

            if plot_df['status'][-1] == "underperform":
                color = 'r'
            else:
                color = 'g'

            plot_df['difference'].plot(label = each_ticker, color = color)


            plt.legend()
        except:
            pass
    """
    #plt.show()
    save = gather.replace(' ','').replace('(','').replace(')','').replace('/','')+str('.csv') #creating a file name to save to.
    print(f"Saving to: {save}") #printing out the name of the file
    df.to_csv("test.csv") #importing file information




key_stats()