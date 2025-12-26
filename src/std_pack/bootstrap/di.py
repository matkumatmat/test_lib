# src/std_pack/bootstrap/di.py

from typing import Type, TypeVar, Callable, Any
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from std_pack.domain.entities import BaseEntity
from std_pack.infrastructure.persistence.models import BaseDBModel
from std_pack.infrastructure.persistence.repositories import SqlAlchemyRepository

# Type Generics
T = TypeVar("T", bound=BaseEntity)
M = TypeVar("M", bound=BaseDBModel)

class RepositoryFactory:
    """
    Factory Class untuk membuat dependency Repository secara dinamis.
    Ini adalah 'Lem' yang menyatukan Domain (Pydantic) dan Infra (SQLAlchemy).
    
    Cara Pakai di Router:
    repo: IRepository = Depends(RepositoryFactory(User, UserModel, get_db))
    """

    def __init__(
        self, 
        domain_cls: Type[T], 
        db_model_cls: Type[M],
        session_dependency: Callable[..., Any]
    ):
        """
        Inisialisasi Factory.
        
        Args:
            domain_cls: Class Domain Entity (Pydantic)
            db_model_cls: Class DB Model (SQLAlchemy)
            session_dependency: Fungsi dependency FastAPI yang menghasilkan AsyncSession
        """
        self.domain_cls = domain_cls
        self.db_model_cls = db_model_cls
        self.session_dependency = session_dependency

    def __call__(
        self, 
        session: AsyncSession = Depends(lambda: None) # Placeholder, akan di-override di init
    ) -> SqlAlchemyRepository[T]:
        """
        Method ini yang dipanggil oleh FastAPI saat injection.
        """
        # Hack untuk memanggil dependency dinamis di dalam class
        # Kita tidak bisa langsung pakai Depends(self.session_dependency) di argumen method __call__
        # karena self.session_dependency baru diketahui saat runtime.
        # Jadi, logika pemanggilan session sebenarnya terjadi di level Router
        # atau kita harus memastikan session yang dilempar ke sini sudah benar.
        
        # PENTING:
        # Agar FastAPI mengenali dependency ini dengan benar, cara pakainya sedikit unik.
        # Kita akan mengandalkan mekanisme 'Depends' pada saat instansiasi Factory di Router.
        # Namun, implementasi __call__ di bawah ini adalah versi 'Explicit' yang aman.
        
        return SqlAlchemyRepository(
            session=session,
            domain_cls=self.domain_cls,
            db_model_cls=self.db_model_cls
        )

# Helper function agar sintaks di Router lebih bersih
# Mengatasi limitasi Depends() pada method __call__ class instance
def create_repository_dependency(
    domain_cls: Type[T], 
    db_model_cls: Type[M],
    session_dependency: Callable[..., AsyncSession]
) -> Callable:
    """
    Wrapper function untuk membuat dependency injection yang valid untuk FastAPI.
    """
    async def _dependency(
        session: AsyncSession = Depends(session_dependency)
    ) -> SqlAlchemyRepository[T]:
        return SqlAlchemyRepository(
            session=session,
            domain_cls=domain_cls,
            db_model_cls=db_model_cls
        )
    return _dependency