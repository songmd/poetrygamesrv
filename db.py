import sqlite3

if __name__ == "__main__":
    pg = sqlite3.connect('pg.db')
    pgc = pg.cursor()

    pgc.execute('SELECT id,stem,dynasty,author,title FROM question')

    for id, stem, dynasty, author, title in pgc:
        cursor = pg.cursor()
        cursor.execute('SELECT id FROM poetry WHERE author=? AND full_text LIKE ?',
                       (author, '%' + stem + '%'))
        pid = cursor.fetchone()
        if pid is None:
            print(stem, dynasty, author, title)
        else:
            c = pg.cursor()
            c.execute('UPDATE question SET reference_id = ? WHERE id = ?', (pid[0], id))
        # else:
        #     print(cursor.fetchone())
    pg.commit()
    # poety = sqlite3.connect('guwen_all.db')
    # # question = sqlite3.connect('questions.db')
    # pcursor = poety.cursor()
    # pcursor.execute('SELECT title,zuozhe,chaodai,quanwen,yw,yuny,zy,yiny,zs FROM poetry')
    # for title, zuozhe, chaodai, quanwen, yw, yuny, zy, yiny, zs in pcursor:
    #     yw = yw or yuny or zy or yiny
    #     pgc.execute('''INSERT INTO poetry
    #                   (dynasty,author,title,annotation,full_text,translation)
    #                   VALUES (?,?,?,?,?,?)''', (chaodai, zuozhe, title, zs, quanwen, yw or yuny or zy or yiny))
    # pg.commit()

    # question = sqlite3.connect('questions.db')
    #
    # qc = question.cursor()
    # qc.execute(
    #     'SELECT question,type,answer,option1,option2,option3,option4,dynasty,author,title,tag,grade FROM questions')
    # for question, type, answer, option1, option2, option3, option4, dynasty, author, title, tag, grade in qc:
    #     pgc.execute('''INSERT INTO question
    #                   (stem,type,answer,option1,option2,option3,option4,dynasty,author,title,tags,grade)
    #                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
    #                 (question, type, answer, option1, option2, option3, option4, dynasty, author, title, tag, grade))
    # pg.commit()
