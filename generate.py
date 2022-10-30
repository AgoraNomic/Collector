from sys import argv
from csv import reader, writer
from datetime import datetime, timezone

isReport = "-r" in argv

# Determine timestamp
now = datetime.now(timezone.utc)

# Load state of last report
current_stamps = {}

score_file = 'current.csv'
with open(score_file, 'r') as infile:
    current_stamps_f = reader(infile, delimiter=',', quotechar="\"")
    
    for row in current_stamps_f:
        pl_holdings = {}
        sets = list(map(lambda a, b: [a, b], row[1::2], row[2::2]))
        for s in sets:
            if s[0] != '':
                pl_holdings[s[0]] = int(s[1])
        current_stamps[row[0]] = pl_holdings
print(current_stamps)

# Load and process events since last report
recent_file = 'recent_events.csv'
historical = ""
with open(recent_file, 'r') as infile:
    recent_in = reader(infile, delimiter=',', quotechar="\"")
    next(recent_in)
    
    for row in recent_in: 
        event, player, s_type, source, number, reason, date = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
        
        if player not in current_stamps:
            current_stamps[player] = {}
        print(row)
        
        stamp_str = "stamp"
        if int(number) > 1:
            stamp_str+= "s"
        
        if event == "NEW":
            historical+= date + ": " + player + " granted " + number + " " + s_type + " " + stamp_str + " by " + source + " ("  + reason + ").\n"
            if s_type not in current_stamps[player]:
                current_stamps[player][s_type] = int(number)
            else:
                current_stamps[player][s_type]+= int(number)
        if event == "TRA":
            historical+= date + ": " + player + " given (transferred) " + number + " " + s_type + " " + stamp_str + " by " + source + " (" + reason + ").\n"
            if s_type not in current_stamps[player]:
                current_stamps[player][s_type] = int(number)
            else:
                current_stamps[player][s_type]+= int(number)
            current_stamps[source][s_type]-= int(number)
            if current_stamps[source][s_type] == 0:
                current_stamps[source].pop(s_type)
        
        # If it's a report, put all of this in the history file now that we're done with it
        if isReport:
            historic_file = 'history.csv'
            with open(historic_file, 'a') as outfile:
                outfile.write(','.join(row)+"\n")

# get ready to format current output
current_holdings_str = ""
current_holdings_csv = ""

# sort owners
owners = sorted(current_stamps.keys(), key = lambda s: s.lower())
if 'L&FD' in owners:
    owners.remove('L&FD')
    owners = ['L&FD'] + owners

for owner in owners:
    line = owner + ": \n"
    current_holdings_csv+= owner + ","

    # sort stamps
    stamp_types = sorted(current_stamps[owner].keys(), key = lambda s: s.lower())

    for stamp_type in stamp_types:
        stamp_count = current_stamps[owner][stamp_type]
        stamp_str = "stamp"
        if int(stamp_count) > 1:
            stamp_str+= "s"
        line += "- " + str(stamp_count) + " " + stamp_type + " " + stamp_str + "\n"
        current_holdings_csv+= stamp_type + "," + str(stamp_count) + ","
    current_holdings_csv = current_holdings_csv[:-1] + "\n"
    current_holdings_str += line + "\n"

print(current_holdings_csv)
current_holdings_str = current_holdings_str[:-2]

# Apply map and output report
with open('report.template', 'r') as infile:
    template = infile.read()

report_mapping = {'date': now.strftime('%d %b %Y'), 'stamps': current_holdings_str, 'historical': historical}

report = template.format_map(report_mapping)

if not isReport:
    print(report)
else:
    report_name = now.strftime('%Y-%m-%d')

    # Write the report to the report.txt and its own file
    with open('reports/' + report_name + '.txt', 'w') as ofile:
        ofile.write(report)

    with open('report.txt', 'w') as ofile:
        ofile.write(report)

    # Updates current.csv
    with open('current.csv', 'w') as ofile:
        ofile.write(current_holdings_csv)

    # Update history.csv
    with open ('history.csv', 'a') as ofile:
        ofile.write(historical)
        
    # Empty recent_events.csv
    with open('recent_events.csv', 'w') as ofile:
        ofile.write("EVENT,PLAYER,TYPE,SOURCE,NUMBER,REASON,DATE")
