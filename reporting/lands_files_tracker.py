import warnings
warnings.simplefilter(action='ignore')

import os
import cx_Oracle
import pandas as pd


def connect_to_DB (username,password,hostname):
    """ Returns a connection and cursor to Oracle database"""
    try:
        connection = cx_Oracle.connect(username, password, hostname, encoding="UTF-8")
        print  ("....Successffuly connected to the database")
    except:
        raise Exception('....Connection failed! Please check your login parameters')

    return connection


def import_ats (ats_f):
    """Reads the ATS report into a df"""
    df = pd.read_excel(ats_f)
    
    df['File Number'] = df['File Number'].fillna(0)
    df['File Number'] = df['File Number'].astype(str)
    
    df.rename(columns={'Comments': 'ATS Comments'}, inplace=True)
    
    df.loc[(df['Accepted Date'].isnull()) & 
       (df['Rejected Date'].isnull()) & 
       (df['Submission Review Complete Date'].notnull()),
       'Accepted Date'] = df['Submission Review Complete Date']
    
    for index,row in df.iterrows():
        z_nbr = 7 - len(str(row['File Number']))
        df.loc[index, 'File Number'] = z_nbr * '0' + str(row['File Number'])
        
    for col in df:
        if 'Date' in col:
            df[col] =  pd.to_datetime(df[col],
                                   infer_datetime_format=True,
                                   errors = 'coerce').dt.date
        elif 'Unnamed' in col:
            df.drop(col, axis=1, inplace=True)
        
        else:
            pass
            
    
    return df


def import_titan (tnt_f):
    """Reads the Titan work ledger report into a df"""
    df = pd.read_excel(tnt_f,'TITAN_RPT009',
                       converters={'FILE NUMBER':str})
    
    tasks = ['NEW APPLICATION','REPLACEMENT APPLICATION','AMENDMENT']
    df = df.loc[df['TASK DESCRIPTION'].isin(tasks)]
    
    df.rename(columns={'COMMENTS': 'TANTALIS COMMENTS'}, inplace=True)
 
    del_col = ['ORG. UNIT','MANAGING AGENCY','BCGS','LEGAL DESCRIPTION',
              'FDISTRICT','ADDRESS LINE 1','ADDRESS LINE 2','ADDRESS LINE 3',
              'CITY','PROVINCE','POSTAL CODE','COUNTRY','STATE','ZIP CODE']
    
    for col in df:
        if 'DATE' in col:
            df[col] =  pd.to_datetime(df[col],
                                   infer_datetime_format=True,
                                   errors = 'coerce').dt.date
        elif 'Unnamed' in col:
            df.drop(col, axis=1, inplace=True)
        
        elif col in del_col:
            df.drop(col, axis=1, inplace=True)
            
        else:
            pass
            
    df.loc[df['PURPOSE'] == 'AQUACULTURE', 'DISTRICT OFFICE'] = 'AQUACULTURE'
    df['DISTRICT OFFICE'] = df['DISTRICT OFFICE'].fillna(value='NANAIMO')
    
    return df

def create_rpt_01(df_tnt,df_ats):
    """ Creates Report 01- New Files in FCBC, not accepted"""
    ats_a = df_ats.loc[df_ats['Authorization Status'] == 'Active']
    #active = ats_a['File Number'].to_list()
    
    df_01= ats_a.loc[(ats_a['Received Date'].notnull()) & (ats_a['Accepted Date'].isnull())]
    
     
    df_01['tempo_join_date']= df_01['Accepted Date'].astype('datetime64[Y]')
    df_tnt['tempo_join_date']= df_tnt['CREATED DATE'].astype('datetime64[Y]')
    
    df_01 = pd.merge(df_01, df_tnt, how='left',
                     left_on=['File Number','tempo_join_date'],
                     right_on=['FILE NUMBER','tempo_join_date'])
    
    df_01.sort_values(by=['Received Date'], ascending=False, inplace=True)
    df_01.reset_index(drop = True, inplace = True)

    return df_01


def create_rpt_02(df_tnt,df_ats):
    """ Creates Report 02- New Files accepted by FCBC, not assigned to a Land Officer"""
    ats_r = df_ats.loc[df_ats['Authorization Status'].isin(['Closed', 'On Hold'])]
    notactive = ats_r['File Number'].to_list()
    
    df_02= df_tnt.loc[(df_tnt['TASK DESCRIPTION'] == 'NEW APPLICATION') &
                      (~df_tnt['FILE NUMBER'].isin(notactive)) &
                      (df_tnt['USERID ASSIGNED TO'].isnull()) &
                      (df_tnt['STATUS'] == 'ACCEPTED')]
      
    df_02['tempo_join_date']= df_02['CREATED DATE'].astype('datetime64[Y]')
    df_ats['tempo_join_date']= df_ats['Accepted Date'].astype('datetime64[Y]')
    
    df_02 = pd.merge(df_02, df_ats, how='left',
                     left_on=['FILE NUMBER','tempo_join_date'],
                     right_on=['File Number','tempo_join_date'])
    
    df_02.sort_values(by=['CREATED DATE'], ascending=False, inplace=True)
    df_02.reset_index(drop = True, inplace = True)
    
    return df_02


def create_rpt_03(df_tnt,df_ats,connection):
    """ Creates Report 03- Expired Tenures autogenerated as replacement application 
                           and not assigned to an LO for Replacement"""
    
    sql = """
     SELECT CROWN_LANDS_FILE
     FROM WHSE_TANTALIS.TA_CROWN_TENURES_SVW
     WHERE RESPONSIBLE_BUSINESS_UNIT = 'VI - LAND MGMNT - VANCOUVER ISLAND SERVICE REGION' 
      AND TENURE_STATUS = 'ACCEPTED'
      AND APPLICATION_TYPE_CDE = 'REP'
      AND CROWN_LANDS_FILE NOT IN (SELECT CROWN_LANDS_FILE 
                                   FROM WHSE_TANTALIS.TA_CROWN_TENURES_SVW
                                   WHERE TENURE_STATUS = 'DISPOSITION IN GOOD STANDING')
    """

    df_q = pd.read_sql(sql,connection)
    rep_l = df_q['CROWN_LANDS_FILE'].to_list()
    
    ats_r = df_ats.loc[df_ats['Authorization Status'].isin(['Closed', 'On Hold'])]
    
    files_r = ats_r['File Number'].to_list()
    
    df_03= df_tnt.loc[(df_tnt['TASK DESCRIPTION']== 'REPLACEMENT APPLICATION') &
                      (df_tnt['FILE NUMBER'].isin(rep_l)) &
                      (~df_tnt['FILE NUMBER'].isin(files_r)) &
                      (df_tnt['USERID ASSIGNED TO'].isnull())]
    
    df_03['tempo_join_date']= df_03['CREATED DATE'].astype('datetime64[Y]')
    df_ats['tempo_join_date']= df_ats['Accepted Date'].astype('datetime64[Y]')
        
        
    df_03 = pd.merge(df_03, df_ats, how='left',
                     left_on=['FILE NUMBER','tempo_join_date'],
                     right_on=['File Number','tempo_join_date'])
        
    df_03.sort_values(by=['RECEIVED DATE'], ascending=False, inplace=True)
    df_03.reset_index(drop = True, inplace = True)
    
    return df_03


def create_rpt_07 (df_tnt,df_ats):
    """ Creates Report 07- Files placed on hold by an LO"""
    df_ats = df_ats.loc[(df_ats['Authorization Status']== 'On Hold') &
                        (df_ats['Accepted Date'].notnull())]
    hold_l = df_ats['File Number'].to_list()
    
    df_07= df_tnt.loc[(df_tnt['STATUS'] == 'ACCEPTED') & 
                      (df_tnt['FILE NUMBER'].isin(hold_l))]

    df_07['tempo_join_date']= df_07['CREATED DATE'].astype('datetime64[Y]')
    df_ats['tempo_join_date']= df_ats['Accepted Date'].astype('datetime64[Y]')
    
    df_07 = pd.merge(df_07, df_ats, how='left',
                     left_on=['FILE NUMBER'],
                     right_on=['File Number'])
    
    df_07.sort_values(by=['CREATED DATE'], ascending=False, inplace=True)
    df_07.reset_index(drop = True, inplace = True)
    
    return df_07


def create_rpt_08 (df_tnt,df_ats):
    """ Creates Report 08- Files with LUR Complete, awaiting approval of recommendation"""
    df_ats = df_ats.loc[df_ats['Authorization Status'].isin(['Active','Closed'])]
    
    df_08= df_tnt.loc[(df_tnt['REPORTED DATE'].notnull()) &
                    (df_tnt['ADJUDICATED DATE'].isnull()) &
                    (df_tnt['STATUS'] == 'ACCEPTED')]

    df_08['tempo_join_date']= df_08['CREATED DATE'].astype('datetime64[Y]')
    df_ats['tempo_join_date']= df_ats['Accepted Date'].astype('datetime64[Y]')
    
    df_08 = pd.merge(df_08, df_ats, how='left',
                     left_on=['FILE NUMBER','tempo_join_date'],
                     right_on=['File Number','tempo_join_date'])
    
    df_08.sort_values(by=['REPORTED DATE'], ascending=False, inplace=True)
    df_08.reset_index(drop = True, inplace = True)
    
    return df_08


def create_rpt_09 (df_tnt,df_ats):
    """ Creates Report 09- Files with decision made, awaiting offer"""
    df_ats = df_ats.loc[df_ats['Authorization Status'].isin(['Active','Closed'])]
    
    df_09= df_tnt.loc[(df_tnt['ADJUDICATED DATE'].notnull()) &
                     (df_tnt['OFFERED DATE'].isnull()) &
                     (df_tnt['STATUS'] == 'ACCEPTED')]

    df_09['tempo_join_date']= df_09['CREATED DATE'].astype('datetime64[Y]')
    df_ats['tempo_join_date']= df_ats['Accepted Date'].astype('datetime64[Y]')
    
    df_09 = pd.merge(df_09, df_ats, how='left',
                     left_on=['FILE NUMBER','tempo_join_date'],
                     right_on=['File Number','tempo_join_date'])
    
    df_09.sort_values(by=['ADJUDICATED DATE'], ascending=False, inplace=True)
    df_09.reset_index(drop = True, inplace = True)
    
    return df_09


def create_rpt_10 (df_tnt,df_ats):
    """ Creates Report 10- Files with offer made, awaiting acceptance"""
    df_ats = df_ats.loc[df_ats['Authorization Status'].isin(['Active','Closed'])]
    df_10= df_tnt.loc[(df_tnt['OFFERED DATE'].notnull()) &
                      (df_tnt['OFFER ACCEPTED DATE'].isnull())&
                      (df_tnt['STATUS'] == 'OFFERED')]
    
    df_10['tempo_join_date']= df_10['CREATED DATE'].astype('datetime64[Y]')
    df_ats['tempo_join_date']= df_ats['Accepted Date'].astype('datetime64[Y]')
    
    df_10 = pd.merge(df_10, df_ats, how='left',
                     left_on=['FILE NUMBER','tempo_join_date'],
                     right_on=['File Number','tempo_join_date'])
    
    df_10.sort_values(by=['OFFERED DATE'], ascending=False, inplace=True)
    df_10.reset_index(drop = True, inplace = True)
    
    return df_10


def create_rpt_11 (df_tnt,df_ats):
    """ Creates Report 11- Files with offer accepted"""
    df_ats = df_ats.loc[df_ats['Authorization Status'].isin(['Active','Closed'])]
    df_11= df_tnt.loc[(df_tnt['OFFER ACCEPTED DATE'].notnull()) &
                      (df_tnt['STATUS'] == 'OFFER ACCEPTED')]
    
    df_11['tempo_join_date']= df_11['CREATED DATE'].astype('datetime64[Y]')
    df_ats['tempo_join_date']= df_ats['Accepted Date'].astype('datetime64[Y]')
    
    df_11 = pd.merge(df_11, df_ats, how='left',
                     left_on=['FILE NUMBER','tempo_join_date'],
                     right_on=['File Number','tempo_join_date'])
    
    df_11.sort_values(by=['OFFER ACCEPTED DATE'], ascending=False, inplace=True)
    df_11.reset_index(drop = True, inplace = True)
    
    return df_11


def set_rpt_colums (df_ats, dfs):
    """ Set the columns"""
    cols = ['Region Name',
         'Business Area',
         'DISTRICT OFFICE',
         'FILE NUMBER',
         'TYPE',
         'SUBTYPE',
         'PURPOSE',
         'SUBPURPOSE',
         'Authorization Status',
         'STATUS',
         'TASK DESCRIPTION',
         'FCBC Assigned To',
         'USERID ASSIGNED TO',
         'OTHER EMPLOYEES ASSIGNED TO',
         'FN Consultation Lead',
         'Adjudication Lead',
         'PRIORITY CODE',
         'Received Date',
         'RECEIVED DATE',
         'Accepted Date',
         'CREATED DATE',
         'Acceptance Complete Net Processing Time',
         'Submission Review Complete Date',
         'Submission Review Net Processing Time',
         'LAND STATUS DATE',
         'First Nation Start Date',
         'First Nation Completion Date',
         'FN Consultation Net Time',
         'Technical Review Complete Date',
         'REPORTED DATE',
         'Technical Review Complete Net Processing Time',
         'ADJUDICATED DATE',
         'OFFERED DATE',
         'OFFER ACCEPTED DATE',
         'Total Processing Time',
         'Total On Hold Time',
         'Net Processing Time',
         'CLIENT NAME',
         'LOCATION',
         'TANTALIS COMMENTS',
         'ATS Comments']
    
    dfs[0] = dfs[0][list(df_ats.columns)[:14]]
    dfs[0].columns = [x.upper() for x in dfs[0].columns]
    
    dfs_f = [dfs[0]]   
    
    for df in dfs[1:]:
        df = df[cols]
        df['Region Name'] = 'WEST COAST'
        df['Business Area'] = 'LANDS'

        df.rename({'Authorization Status': 'ATS STATUS', 
                   'STATUS': 'TANTALIS STATUS',
                   'TASK DESCRIPTION': 'APPLICATION TYPE',
                   'USERID ASSIGNED TO': 'EMPLOYEE ASSIGNED TO'}, 
                  axis=1, inplace=True)

        df.columns = [x.upper() for x in df.columns]
        
        dfs_f.append (df)
    
    return dfs_f
        

#def main()

print ('Connecting to BCGW.')
hostname = 'bcgw.bcgov/idwprod1.bcgov'
bcgw_user = os.getenv('bcgw_user')
bcgw_pwd = os.getenv('bcgw_pwd')
connection = connect_to_DB (bcgw_user,bcgw_pwd,hostname)


print ('Reading Input files')
print('...ats report')
ats_f = 'ats_20230306.xlsx'
print('...titan report')
df_ats = import_ats (ats_f)
tnt_f = 'TITAN_RPT009.xlsx'
df_tnt = import_titan (tnt_f)


print('Creating Reports.')
dfs = []

print('...report 01')
df_01 = create_rpt_01 (df_tnt,df_ats)
dfs.append(df_01)

print('...report 02')
df_02 = create_rpt_02 (df_tnt,df_ats)
dfs.append(df_02)

print('...report 03')
df_03 = create_rpt_03 (df_tnt,df_ats,connection)
dfs.append(df_03)

print('...report 07')
df_07 = create_rpt_07 (df_tnt,df_ats)
dfs.append(df_07)

print('...report 08')
df_08 = create_rpt_08 (df_tnt,df_ats)
dfs.append(df_08)

print('...report 09')
df_09 = create_rpt_09 (df_tnt,df_ats)
dfs.append(df_09)

print('...report 10')
df_10 = create_rpt_10 (df_tnt,df_ats)
dfs.append(df_10)

print('...report 11')
df_11 = create_rpt_11 (df_tnt,df_ats)
dfs.append(df_11)

print('Formatting reports')
dfs_f = set_rpt_colums (df_ats, dfs)
