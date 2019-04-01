# sqlalchemy默认底层使用 mysqldb 完成和数据库的连接
# 但是 mysqldb 不支持最新版本的 python 和 mysql 数据库的连接，一般用Pymysql进行替代。
import pymysql
from sqlalchemy import Column, String, Integer, Enum, DateTime, JSON, ForeignKey, Table
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

pymysql.install_as_MySQLdb()

engine = create_engine('mysql://root:YXhxODg0OA==@localhost/wx_app', encoding='utf-8', echo=True)

Session = sessionmaker(bind=engine)
sess = Session()
Base = declarative_base(bind=engine)


class DAO:
    def __enter__(self):
        self._session = Session()
        self._status = 0
        return self

    def __call__(self, *args, **kwargs) -> Session:
        return self._session

    def __exit__(self):
        if self._status == 0:
            self._session.commit()
        elif self._status == 1:
            self._session.close()
        else:
            self._session.rollback()
            self._session.close()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    open_id = Column(String(32), primary_key=True)
    name = Column(String(30))
    school = Column(String(30))
    school_num = Column(String(20))
    role = Column(Enum("teacher", "student", "none", name="user_role_enum", create_type="False"))
    tel = Column(Integer)
    comps = relationship("UserComp", back_populates="user")

    def get_user_info(self):
        return {
            'name': self.name,
            'school': self.school,
            'school_num': self.name,
            'role': self.role,
            'tel': self.tel
        }

    @staticmethod
    def get_user(openid):
        db_sess = Session()
        user = db_sess.query(User).filter_by(open_id=openid).first()
        db_sess.close()
        return user

    @staticmethod
    def new_user(openid):
        db_sess = Session()
        db_sess.add(User(open_id=openid))
        db_sess.commit()

    @staticmethod
    def update_user_info(**kwargs):
        pass


comp_tag_table = Table('comp_tag', Base.metadata,
                       Column("comp_id", Integer, ForeignKey("comp.id")),
                       Column("tag_id", Integer, ForeignKey("tag.id"))
                       )


class Comp(Base):
    __tablename__ = 'comp'

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(
        Enum("pend", "open", "prepared", "racing", "end", "result", name="comp_status_enum", create_type=False))
    time_open = Column(DateTime)
    time_close = Column(DateTime)
    time_begin = Column(DateTime)
    time_end = Column(DateTime)
    tags = relationship("Tag", secondary=comp_tag_table, back_populates="comps")
    info = Column(JSON)
    users = relationship("UserComp", back_populates="comp")


class Tag(Base):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True, autoincrement=True)
    comps = relationship("Comp", secondary=comp_tag_table, back_populates="tags")
    name = Column(String(10))


class UserComp(Base):
    __tablename__ = 'user_comp'

    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    comp_id = Column(Integer, ForeignKey("comp.id"), primary_key=True)
    privileges = Column(Enum("manager", "participate", "watch", name="uc_priv_enum", create_type=False))
    user = relationship("User", back_populates="comps")
    comp = relationship("Comp", back_populates="users")


Base.metadata.create_all()
