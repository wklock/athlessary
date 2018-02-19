import unittest

from Utils.db import Database
from Utils.util_basic import create_workout

# It's okay that this doesn't exist because the database initializer ensures it's setup properly
db = Database("test-database.db")


def create_user(user_name):
    # add user
    sample_col_names = ['username', 'first', 'last', 'password', 'address', 'has_car', 'num_seats']
    sample_data = [user_name, 'hello', 'bye', '123', '1 east green', True, 3]
    table = 'users'
    row_id = db.insert(table, sample_col_names, sample_data)
    return row_id


def clean_up_table(table, pk):
    # empty users
    rows = db.select(table, [pk], fetchone=False)
    for _id in rows:
        db.delete_entry(table, pk, _id[pk])


class TestAutoDB(unittest.TestCase):
    """
    Test automated insert, select, and update sql creation
    """

    def test_insert(self):
        # create a user
        row_id = create_user('user1')

        # assert it exists and that it has a row_id > 0
        self.assertGreater(row_id, 0, 'row id must be greater than 0')

        # delete user
        clean_up_table('users', 'id')

        # assert empty
        self.assertEqual([], db.select('users', ['ALL'], fetchone=False))

    def test_select(self):

        # insert new row
        cur_username = '123a4bob112342'
        first_name = 'jimmy'
        last_name = 'ricky'
        sample_col_names = ['username', 'first', 'last', 'password', 'address', 'has_car', 'num_seats']
        sample_data = [cur_username, first_name, last_name, '123', '1 east green', True, 4]
        table = 'users'
        row_id = db.insert(table, sample_col_names, sample_data)

        # select ALL by 1 parameter (ID)
        row = db.select(table, ['ALL'], ['id'], [row_id])
        print(row)
        self.assertEqual(cur_username, row['username'], 'incorrect username')

        # select 1 parameter (first name) by 1 parameter (ID)
        row = db.select(table, ['first'], ['id'], [row_id])
        print(row)
        self.assertEqual(first_name, row['first'], 'incorrect first name')

        # select 2 parameters (first, last) by 1 parameter (ID)
        row = db.select(table, ['first', 'last'], ['id'], [row_id])
        print(row)
        self.assertEqual(first_name, row['first'], 'incorrect first name')
        self.assertEqual(last_name, row['last'], 'incorrect last name')

        # select 2 parameters (first, last) by 2 parameters (ID, username)
        row = db.select(table, ['first', 'last'], ['id', 'username'], [row_id, cur_username])
        print(row)
        self.assertEqual(first_name, row['first'], 'incorrect first name')
        self.assertEqual(last_name, row['last'], 'incorrect last name')

        # insert another row
        cur_username = 'jiam1'
        first_name = 'jane'
        last_name = 'robby'
        sample_col_names = ['username', 'first', 'last', 'password', 'address', 'has_car', 'num_seats']
        sample_data = [cur_username, first_name, last_name, '123', '1 east green', True, 3]
        table = 'users'
        row_id = db.insert(table, sample_col_names, sample_data)

        # test fetch many without where clause
        rows = db.select(table, ['id'], fetchone=False)
        self.assertEqual(2, len(rows))
        print(rows)

        # test fetch many with where clause
        rows = db.select(table, ['id'], ['address'], ['1 east green'], fetchone=False)
        self.assertEqual(2, len(rows))
        print(rows)

        # test different operator (one operator)
        rows = db.select(table, ['username', 'id'], ['id'], [10000], ['<'], fetchone=False)
        self.assertEqual(2, len(rows))
        print(rows)

        # test different operator (two operators)
        rows = db.select(table, ['username', 'id'], ['id', 'address'], [10000, '1 east green'], ['<', '='], fetchone=False)
        self.assertEqual(2, len(rows))
        print(rows)

        # test different operator (three operators)
        rows = db.select(table, ['username', 'id'], ['id', 'address', 'num_seats'], [10000, '1 east green', '1'], ['<', '=', '>'],
                              fetchone=False)
        self.assertEqual(2, len(rows))
        print(rows)

        # TODO test oder by

        # delete all entries
        clean_up_table('users', 'id')

        # assert empty
        rows = db.select(table, ['id'], fetchone=False)
        self.assertEqual([], rows, 'not all deleted!!')
        print(rows)

    def test_update(self):
        # insert new row
        table = 'users'
        row_id = create_user('new_user')

        # update picture field
        db.update(table, ['picture'], ['my pic'], ['id'], [row_id], ['='])

        row = db.select(table, ['picture'], ['id'], [row_id])

        # assert picture has changed
        self.assertEqual(row['picture'], 'my pic', 'does not match picture')

        # clean up
        clean_up_table('users', 'id')

        # assert empty
        self.assertEqual([], db.select('users', ['ALL'], fetchone=False))


class TestDBSpecific(unittest.TestCase):
    """
    test queries for specific purposes
    """

    def test_aggregate_workouts(self):
        # add user
        row_id = create_user('a_new_user')

        # add workout
        meters = [2000, 2000]
        minutes = [6, 7]
        seconds = [58, 1]
        by_distance = True
        create_workout(row_id, db, meters, minutes, seconds, by_distance)

        # aggregate the workouts
        res = db.get_aggregate_workouts_by_name(row_id, '2x2000m')
        print(res)
        self.assertIsNotNone(res, 'result should not be none')
        self.assertEqual(res[0]['total_seconds'], 419.5, 'seconds are wrong')

        # add second workout
        meters = [2000, 2000]
        minutes = [6, 6]
        seconds = [58, 54]
        by_distance = True
        create_workout(row_id, db, meters, minutes, seconds, by_distance)

        res = db.get_aggregate_workouts_by_name(row_id, '2x2000m')

        self.assertEqual(2, len(res), 'result should not be none')
        self.assertEqual(res[1]['total_seconds'], 416, 'seconds are wrong')

        # clean up pieces
        clean_up_table('erg', 'erg_id')
        self.assertEqual(0, len(db.select('erg', ['ALL'], fetchone=False)))

        # clean up workouts
        clean_up_table('workout', 'workout_id')
        self.assertEqual(0, len(db.select('workout', ['ALL'], fetchone=False)))

        # clean up users
        clean_up_table('users', 'id')
        self.assertEqual(0, len(db.select('users', ['ALL'], fetchone=False)))

    def test_get_workout_names(self):
        # add user
        row_id = create_user('a_user')

        names = db.find_all_workout_names(row_id)
        self.assertEqual([], names, 'names array is empty')

        # clean up users
        clean_up_table('users', 'id')
        self.assertEqual(0, len(db.select('users', ['ALL'], fetchone=False)))

    def test_get_total_meters(self):
        # add user
        user_id = create_user('user123')

        meters = [2000, 2000]
        minutes = [6, 7]
        seconds = [58, 1]
        by_distance = True
        create_workout(user_id, db, meters, minutes, seconds, by_distance)

        total_meters = db.get_total_meters(user_id)['total_meters']
        self.assertEqual(total_meters, 4000, 'number of meters does not match up')

        # clean up pieces
        clean_up_table('erg', 'erg_id')
        self.assertEqual(0, len(db.select('erg', ['ALL'], fetchone=False)))

        # clean up workouts
        clean_up_table('workout', 'workout_id')
        self.assertEqual(0, len(db.select('workout', ['ALL'], fetchone=False)))

        # clean up users
        clean_up_table('users', 'id')
        self.assertEqual(0, len(db.select('users', ['ALL'], fetchone=False)))

    def test_trigger_delete_workout_after_all_pieces_are_deleted(self):
        # add a user
        user_id = create_user('123user123')

        # create workouts
        meters = [2000, 2000]
        minutes = [6, 7]
        seconds = [58, 1]
        by_distance = True
        create_workout(user_id, db, meters, minutes, seconds, by_distance)

        rows = db.select('erg', ['ALL'], fetchone=False)

        # assert that there are 2 erg pieces
        self.assertEqual(len(rows), 2, 'incorrect length of rows')

        # assert that there is one workout
        self.assertEqual(len(db.select('workout', ['ALL'], fetchone=False)), 1, 'there is one workout')

        # delete one of the erg pieces
        db.delete_entry('erg', 'erg_id', rows[0]['erg_id'])

        rows = db.select('erg', ['ALL'], fetchone=False)

        # assert that there is only one erg piece
        self.assertEqual(len(rows), 1, 'there should only be 1 row')

        # assert that there is STILL one workout
        self.assertEqual(len(db.select('workout', ['ALL'], fetchone=False)), 1, 'there is one workout')

        # delete the other erg piece
        db.delete_entry('erg', 'erg_id', rows[0]['erg_id'])

        # assert that there are no erg pieces
        self.assertEqual(len(db.select('erg', ['ALL'], fetchone=False)), 0, 'erg table is empty')

        # assert that there are no workouts
        self.assertEqual(len(db.select('workout', ['ALL'], fetchone=False)), 0, 'workout table is empty')

        # clean up users
        clean_up_table('users', 'id')
        self.assertEqual(0, len(db.select('users', ['ALL'], fetchone=False)))

    def test_trigger_del_pieces_after_del_workout(self):
        # add a user
        user_id = create_user('123user123')

        # create workouts
        meters = [2000, 2000]
        minutes = [6, 7]
        seconds = [52, 10]
        by_distance = True
        create_workout(user_id, db, meters, minutes, seconds, by_distance)

        # delete all workouts
        clean_up_table('workout', 'workout_id')

        # assert that there are no workouts
        self.assertEqual(len(db.select('workout', ['ALL'], fetchone=False)), 0, 'workout table is empty')

        # assert that there are no erg pieces
        self.assertEqual(len(db.select('erg', ['ALL'], fetchone=False)), 0, 'erg table is empty')

        # clean up users
        clean_up_table('users', 'id')
        self.assertEqual(0, len(db.select('users', ['ALL'], fetchone=False)))