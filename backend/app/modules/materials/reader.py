from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pypdf import PdfReader

from app import models as m
from app.db.session import get_db
from app.shared.dependencies import material_for
from app.core.security import current_user

router = APIRouter(tags=["reader"])


@router.get("/materials/{material_id}/pages")
def material_pages(material_id: int, db=Depends(get_db), user=Depends(current_user)):
    material = material_for(db, material_id, user.id)
    material.last_opened_at=datetime.now();topic=db.query(m.Topic).filter_by(id=material.topic_id).first()
    if topic:topic.last_opened_at=datetime.now();topic.subject.last_studied_at=datetime.now()
    if not material.pages:
        contents=[]
        if material.file_type=="application/pdf" and material.storage_path and Path(material.storage_path).is_file():
            try: contents=[page.extract_text() or "" for page in PdfReader(material.storage_path).pages]
            except Exception: contents=[]
        elif material.extracted_text: contents=[material.extracted_text]
        if contents:
            db.add_all([m.MaterialPage(material_id=material.id,page_number=index+1,content=content) for index,content in enumerate(contents)])
    db.commit();db.refresh(material)
    return {
        "material_id": material.id,
        "topic_id": material.topic_id,
        "file_name": material.file_name,
        "file_type": material.file_type,
        "page_count": len(material.pages),
        "pages": [{"page_number": page.page_number, "content": page.content} for page in material.pages],
    }


@router.get("/materials/{material_id}/file")
def material_file(material_id: int, db=Depends(get_db), user=Depends(current_user)):
    material = material_for(db, material_id, user.id)
    material.last_opened_at=datetime.now();db.commit()
    if not material.storage_path or not Path(material.storage_path).is_file():
        raise HTTPException(404, "Material file not found")
    return FileResponse(material.storage_path, media_type=material.file_type, filename=material.file_name)


@router.get("/materials/{material_id}/page/{page_number}")
def material_page(material_id: int, page_number: int, db=Depends(get_db), user=Depends(current_user)):
    material = material_for(db, material_id, user.id)
    page = db.query(m.MaterialPage).filter_by(material_id=material.id, page_number=page_number).first()
    if not page:
        raise HTTPException(404, "Page text is not available")
    return {"material_id": material.id, "page_number": page.page_number, "content": page.content}
