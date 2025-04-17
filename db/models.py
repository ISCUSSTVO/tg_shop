from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime,  Text, func

class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default = func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default = func.now() , onupdate= func.now())


##################Дтаблица админов################################################################
class Admins(Base):
    __tablename__ = 'admins'

    id: Mapped[int] = mapped_column(primary_key = True, autoincrement = True)
    username: Mapped[str] = mapped_column(String)
##################Дтаблица Юзеров################################################################
class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key = True, autoincrement = True)
    user_id: Mapped[int] = mapped_column(Integer)
##################Дтаблица Юзеров################################################################
class Spam(Base):
    __tablename__ = 'rassilka'

    id: Mapped[int] = mapped_column(primary_key = True, autoincrement = True)
    smska: Mapped[str] = mapped_column(String)
##################таблица аккаунтов################################################################aa
class Catalog(Base):
    __tablename__ = 'promocodes_cat'

    id: Mapped[int] = mapped_column(primary_key = True, autoincrement = True)
    name: Mapped[str] = mapped_column(String(15))
    promocode: Mapped[str] = mapped_column(String(70), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    price: Mapped[int]  = mapped_column(Integer)
    discount: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


##################таблица банеры ################################################################
class Banner(Base):
    __tablename__ = 'banner'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(15), unique=True)
    image: Mapped[str] = mapped_column(String(150), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

##################Промокоды на скидоны################################################################
class Promokodes(Base):
    __tablename__ = 'promocodes'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    promocode: Mapped[str] = mapped_column(String(15), unique=False)
    discount: Mapped[int] = mapped_column(Integer(), nullable=False)
    usage: Mapped[int] = mapped_column(Integer(), nullable=False)

######################таблица использования промокодов#############################################################
class PromocodeUsage(Base): 
    __tablename__ = 'promocode_usage'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    promocode: Mapped[str] = mapped_column(String(15), nullable=False)
    user_id: Mapped[int] = mapped_column(String, nullable=False)

######################таблица корзины#############################################################
class Cart(Base):
    __tablename__ = 'cart'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer(), nullable=False)
    product_name: Mapped[str] = mapped_column(String(15), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
