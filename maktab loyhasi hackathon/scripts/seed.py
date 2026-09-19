from backend.app.db import init_db, engine, Submission, GradeRecord
from sqlmodel import Session


def seed():
    init_db()
    with Session(engine) as s:
        s.add(Submission(student_id='s001', course='Matematika', content='Talabaning boshlangich insho.'))
        s.add(Submission(student_id='s002', course='Matematika', content='Yana bir talaba insho.'))
        s.commit()
        subs = s.exec(Submission.select()).all()
        for sub in subs:
            s.add(GradeRecord(submission_id=sub.id, total_score=75, details='{"rubric": []}'))
        s.commit()


if __name__ == '__main__':
    seed()
    print('Seed completed')
