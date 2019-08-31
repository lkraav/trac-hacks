
def do_upgrade(env, ver, cursor):
    # Round date to full days (integer division is truncate, so add half a day to get rounding instead)
    cursor.execute("""
        UPDATE timetrackinglogs
        SET date = ((date + 12*60*60*1000*1000)/(24*60*60*1000*1000))*(24*60*60*1000*1000)
        """)
