from models import users

newUsers = users.create([
    {
        'name': 'Person 1'
    },
    {
        'name': 'Person 2'
    }
])

newUser = users.create({
    'name': 'Person 3'
})


for user in newUsers:
    print(user.read()) #

    # update method can be used with record directly
    user.update({
        'name': 'Ragab'
    })

# update method can also take multiple records with id and returns True if all records updated.
users.update([
    {
        'id': id,
        'name': 'Mohammed'
    }
])

# search method takes polish notation domain and returns list of records
user_records = users.search([
    ('name', '=', 'Mohammed')
])

for user in user_records:
    # read method returns dictionary or list of dictionary
    print(user.read())

# delete method takes a list of ids to be deleted or nothing in case of used with single record returns boolean
for user in user_records:
    user.delete()
