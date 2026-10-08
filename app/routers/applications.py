from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, select

from app.deps import CurrentUser, DbSession
from app.models import Application, ApplicationStatus
from app.schemas import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationPage,
    ApplicationUpdate,
    Stats,
)

router = APIRouter(prefix="/applications", tags=["applications"])

SORT_FIELDS = {
    "created_at": Application.created_at,
    "applied_on": Application.applied_on,
    "company": Application.company,
}

# Statuses that mean the company actually replied.
RESPONDED = {ApplicationStatus.interviewing, ApplicationStatus.offer, ApplicationStatus.rejected}


def _get_owned(db: DbSession, user: CurrentUser, application_id: int) -> Application:
    """Fetch an application that belongs to this user, or 404.

    We return 404 (not 403) for other users' records so the API doesn't
    reveal which ids exist.
    """
    app = db.get(Application, application_id)
    if app is None or app.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
    return app


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationCreate, db: DbSession, user: CurrentUser) -> Application:
    data = payload.model_dump()
    if data["job_url"] is not None:
        data["job_url"] = str(data["job_url"])  # HttpUrl -> plain string for the DB
    app = Application(**data, owner_id=user.id)
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


@router.get("", response_model=ApplicationPage)
def list_applications(
    db: DbSession,
    user: CurrentUser,
    status_filter: Annotated[ApplicationStatus | None, Query(alias="status")] = None,
    q: Annotated[str | None, Query(description="Search company or position")] = None,
    sort: Literal["created_at", "applied_on", "company"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApplicationPage:
    stmt = select(Application).where(Application.owner_id == user.id)
    if status_filter:
        stmt = stmt.where(Application.status == status_filter)
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            func.lower(Application.company).like(pattern)
            | func.lower(Application.position).like(pattern)
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    column = SORT_FIELDS[sort]
    stmt = stmt.order_by(column.asc() if order == "asc" else column.desc(), Application.id)
    items = db.scalars(stmt.limit(limit).offset(offset)).all()

    return ApplicationPage(
        total=total,
        limit=limit,
        offset=offset,
        items=[ApplicationOut.model_validate(i) for i in items],
    )


@router.get("/stats", response_model=Stats)
def application_stats(db: DbSession, user: CurrentUser) -> Stats:
    rows = db.execute(
        select(Application.status, func.count())
        .where(Application.owner_id == user.id)
        .group_by(Application.status)
    ).all()
    by_status = {s: 0 for s in ApplicationStatus}
    by_status.update({s: n for s, n in rows})

    total = sum(by_status.values())
    submitted = total - by_status[ApplicationStatus.wishlist]
    responded = sum(by_status[s] for s in RESPONDED)
    rate = round(responded / submitted, 3) if submitted else 0.0
    return Stats(total=total, by_status=by_status, response_rate=rate)


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(application_id: int, db: DbSession, user: CurrentUser) -> Application:
    return _get_owned(db, user, application_id)


@router.patch("/{application_id}", response_model=ApplicationOut)
def update_application(
    application_id: int, payload: ApplicationUpdate, db: DbSession, user: CurrentUser
) -> Application:
    app = _get_owned(db, user, application_id)
    changes = payload.model_dump(exclude_unset=True)
    if "job_url" in changes and changes["job_url"] is not None:
        changes["job_url"] = str(changes["job_url"])
    for field, value in changes.items():
        setattr(app, field, value)
    db.commit()
    db.refresh(app)
    return app


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(application_id: int, db: DbSession, user: CurrentUser) -> Response:
    app = _get_owned(db, user, application_id)
    db.delete(app)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
