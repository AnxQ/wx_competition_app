# sqlalchemy默认底层使用 mysqldb 完成和数据库的连接
# 但是 mysqldb 不支持最新版本的 python 和 mysql 数据库的连接，一般用Pymysql进行替代。
import enum

import pymysql
from sqlalchemy import Column, String, Integer, Enum, DateTime, JSON, ForeignKey, Table, BigInteger, Boolean
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from config import current_config

pymysql.install_as_MySQLdb()

engine = create_engine(current_config.DatabaseURL, encoding='utf-8', echo=True)

Session = sessionmaker(bind=engine)
sess = Session()

Base = declarative_base(bind=engine)

max_page_limit = 10

"""
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
"""


class GroupPrivilege(enum.Enum):
    creator = 0
    admin = 1
    member = 2


class CompPrivilege(enum.Enum):
    creator = 0
    admin = 1
    member = 2
    watch = 3


class UserGender(enum.Enum):
    male = 0
    female = 1


class UserRole(enum.Enum):
    none = 0
    teacher = 1
    student = 2


class CompStatus(enum.Enum):
    pend = 1
    open = 2
    prepared = 3
    racing = 4
    end = 5
    result = 0


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    open_id = Column(String(32), primary_key=True)
    name = Column(String(30))
    school = Column(String(30))
    school_num = Column(String(20))
    role = Column(Enum(UserRole, name="user_role_enum", create_type=False))
    tel = Column(BigInteger)
    gender = Column(Enum(UserGender, name="user_gender_enum", create_type=False))
    settings = Column(JSON,
                      default={"hide_gender": False,
                               "hide_name": False,
                               "hide_school_num": True,
                               "allow_bejoin": True,
                               "allow_find": True})
    motto = Column(String(50))
    comps = relationship("UserComp", back_populates="user")
    groups = relationship("UserGroup", back_populates="user")

    @property
    def info_dict(self):
        return {
            'name': self.name,
            'school': self.school,
            'school_num': self.school_num,
            'role': self.role.value if self.role else None,
            'tel': self.tel,
            'gender': self.gender.value if self.gender else None,
            'settings': self.settings
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

    def update_user_info(self, data):
        db_sess = Session()
        pre = db_sess.query(User).filter_by(id=self.id).first()
        pre.name = data['name']
        pre.school = data['school']
        pre.school_num = data['school_num']
        pre.role = data['role']
        pre.tel = data['tel']
        pre.gender = data['gender']
        pre.settings = data['settings']
        db_sess.commit()


comp_tag_table = Table('comp_tag', Base.metadata,
                       Column("comp_id", Integer, ForeignKey("comp.id")),
                       Column("tag_id", Integer, ForeignKey("tag.id"))
                       )


class Tag(Base):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True, autoincrement=True)
    comps = relationship("Comp", secondary=comp_tag_table, back_populates="tags")
    name = Column(String(10))

    @property
    def tag_dict(self):
        return {
            'id': self.id,
            'comps': self.comps,
            'name': self.name
        }


class Comp(Base):
    __tablename__ = 'comp'

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Enum(CompStatus, name="comp_status_enum", create_type=False))
    time_open = Column(DateTime)
    time_close = Column(DateTime)
    time_begin = Column(DateTime)
    time_end = Column(DateTime)
    tags = relationship("Tag", secondary=comp_tag_table, back_populates="comps")
    platform_manage = Column(Boolean)
    official_link = Column(String(100))
    info = Column(JSON,
                  default={"name": "",
                           "description": "",
                           "reward": ""})
    users = relationship("UserComp", back_populates="comp")

    @property
    def comp_dict(self):
        return {
            'id': self.id,
            'status': self.status.value if self.status else None,
            'time_open': self.time_open,
            'time_close': self.time_close,
            'time_begin': self.time_begin,
            'time_end': self.time_end,
            'info': self.info,
            'platform_manage': self.platform_manage,
            'official_link': self.official_link,
            'tags': list(map(lambda x: x.tag_dict, self.tags))
        }

    @staticmethod
    def get_comp(comp_filters, tags, page=0):
        """
        去重查询含有当前标签，满足当前过滤器的comp列表
        :param comp_filters:
        :param tags:
        :param page:
        :return:
        """
        db_session = Session()
        if not tags:
            staging_tags = db_session.query(Tag).filter(Tag.name in tags)
            staging_comps = db_session.query(Comp).filter(staging_tags in Comp.tags)
        staging_comps = db_session.query(Comp) \
            .filter(comp_filters) \
            .order_by(Comp.time_open) \
            .offset(page * max_page_limit) \
            .limit(max_page_limit).all()
        return list(map(lambda x: x.comp_dict, staging_comps))


class UserComp(Base):
    __tablename__ = 'user_comp'

    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    comp_id = Column(Integer, ForeignKey("comp.id"), primary_key=True)
    privileges = Column(Enum(CompPrivilege, name="uc_priv_enum", create_type=False))
    user = relationship("User", back_populates="comps")
    comp = relationship("Comp", back_populates="users")


class Group(Base):
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20))
    motto = Column(String(100))
    settings = Column(JSON,
                      default={"max_member": 20,
                               "allow_join": True})
    users = relationship("UserGroup", back_populates="group")


class UserGroup(Base):
    __tablename__ = 'user_group'

    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    group_id = Column(Integer, ForeignKey("group.id"), primary_key=True)
    privileges = Column(Enum(GroupPrivilege, name="ug_priv_enum", create_type=False))
    user = relationship("User", back_populates="groups")
    group = relationship("Group", back_populates="users")


Base.metadata.create_all()
