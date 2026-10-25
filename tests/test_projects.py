import zipfile
import io
from app.models.project import Project


def test_projects_catalog(client):
    """Verifies that the capstone projects list renders."""
    resp = client.get("/projects")
    assert resp.status_code == 200
    assert b"Portfolio-Grade Capstone Projects" in resp.data


def test_project_detail_and_zip_export(client, app):
    """Verifies viewing a project detail and downloading clean ZIP archive."""
    with app.app_context():
        p = Project.query.first()
        assert p is not None

        # Detail route
        resp = client.get(f"/projects/{p.slug}")
        assert resp.status_code == 200
        assert p.title.encode("utf-8") in resp.data

        # Export ZIP route
        zip_resp = client.get(f"/api/projects/{p.slug}/export")
        assert zip_resp.status_code == 200
        assert zip_resp.mimetype == "application/zip"

        # Verify ZIP contains README and files, and excludes secrets
        zf = zipfile.ZipFile(io.BytesIO(zip_resp.data))
        namelist = zf.namelist()
        assert any("README.md" in n for n in namelist)
        assert not any(".env.local" in n for n in namelist)
