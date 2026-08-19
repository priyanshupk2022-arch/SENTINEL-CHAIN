import random
import string
import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/chaos", tags=["chaos"])

class ChaosRequest(BaseModel):
    level: int
    target_url: str

def get_random_hash(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def inject_level_1(soup: BeautifulSoup) -> BeautifulSoup:
    """CSS class hash scramble."""
    for tag in soup.find_all(True):
        classes = tag.get('class')
        if classes:
            new_classes = [f"{cls}-{get_random_hash(6)}" for cls in classes]
            tag['class'] = new_classes
    return soup

def inject_level_2(soup: BeautifulSoup) -> BeautifulSoup:
    """Parent-child hierarchy wrapper nesting."""
    # Apply level 1 first as cumulative? The prompt doesn't explicitly say.
    # Usually chaos levels are cumulative or independent, let's just do Level 2 logic.
    # We will wrap random leaf or text-containing nodes in multiple divs.
    elements_to_wrap = soup.find_all(['p', 'span', 'div', 'button', 'a'])
    # limit to some random elements to avoid too deep recursion
    import random
    if elements_to_wrap:
        sample_size = min(len(elements_to_wrap), 10)
        for tag in random.sample(elements_to_wrap, sample_size):
            wrapper = soup.new_tag('div')
            wrapper['class'] = f"wrapper-{get_random_hash()}"
            inner_wrapper = soup.new_tag('div')
            inner_wrapper['class'] = f"inner-{get_random_hash()}"
            
            # Wrap
            tag.wrap(wrapper)
            tag.wrap(inner_wrapper)
    return soup

def inject_level_3(soup: BeautifulSoup) -> BeautifulSoup:
    """Closed Shadow DOM & honeypot decoy fields."""
    # Insert honeypot forms
    body = soup.find('body')
    if body:
        honeypot = soup.new_tag('input')
        honeypot['type'] = 'text'
        honeypot['name'] = 'honeypot_decoy'
        honeypot['style'] = 'display:none; opacity:0; position:absolute; left:-9999px;'
        honeypot['tabindex'] = '-1'
        body.insert(0, honeypot)

        # Wrap body content in a closed shadow DOM
        template = soup.new_tag('template')
        template['shadowrootmode'] = 'closed'
        
        # move all body children into template
        for child in list(body.children):
            if child != honeypot:
                template.append(child.extract())
        
        body.append(template)
        
    return soup

@router.post("/inject")
async def inject_chaos(req: ChaosRequest):
    if req.level not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="Level must be 1, 2, or 3")
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(req.target_url)
            response.raise_for_status()
            html = response.text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")

    soup = BeautifulSoup(html, 'html.parser')
    
    if req.level == 1:
        soup = inject_level_1(soup)
    elif req.level == 2:
        soup = inject_level_2(soup)
    elif req.level == 3:
        soup = inject_level_3(soup)

    return {"status": "success", "mutated_html": str(soup)}
