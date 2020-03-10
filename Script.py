import xmlrpc.client


#Connexion :

url = "http://localhost:8013"
db = "New"
username = "Bouharra.mehdi@hotmail.com"
password = "Mehdi77"

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))

uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

#Recuperation des cours et sessions:

sessions=models.execute_kw(db, uid, password,
    'openacademy.session', 'search_read',
    [[]],
    {'fields': ['name', 'course_id', 'price_per_hour']})  #pour recuperer tous les champs on peut enlever fields 

courses=models.execute_kw(db, uid, password,
    'openacademy.course', 'search_read',
    [[]],
    {'fields': ['name', 'responsible_id']})

#si on veut recuperer les champs de session ou course avec parametres (pas necessaires) :

#models.execute_kw(
#    db, uid, password, 'openacademy.session', 'fields_get',
#    [], {'attributes': ['string', 'help', 'type']})


#models.execute_kw(
#    db, uid, password, 'openacademy.course', 'fields_get',
#    [], {'attributes': ['string', 'help', 'type']})

#Creation de cours et sessions :

id = models.execute_kw(db, uid, password, 'openacademy.course', 'create', [{
    'name': "New Course",
}])

id = models.execute_kw(db, uid, password, 'openacademy.session', 'create', [{
    'name': "Session script ",'course_id':"12"
}])


#On recupere les ids des elements du modele res.partner , on pourra alors choisir des attendees que l'on va affecter a une session :

partners=models.execute_kw(db, uid, password,
    'res.partner', 'search_read',
    [[]],
    {'fields': ['name']}) 

models.execute_kw(db, uid, password, 'openacademy.session', 'write', [[20], {
    'attendee_ids': [7, 9, 10]
}])

#Pour modifier On peut utiliser la meme commande que la derniere utilisee 'write'

#Pour supprimer une session

models.execute_kw(db, uid, password, 'openacademy.session', 'unlink', [[20]])

