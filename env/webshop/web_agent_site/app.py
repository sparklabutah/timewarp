import argparse, json, logging, random, os, sys, socket
from pathlib import Path
from ast import literal_eval
from dotenv import load_dotenv

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    send_from_directory
)

from rich import print

# Load environment variables from .env file
load_dotenv()

from web_agent_site.engine.engine import (
    load_products,
    init_search_engine,
    convert_web_app_string_to_var,
    get_top_n_product_from_keywords,
    get_product_per_page,
    map_action_to_html,
    set_theme,
    END_BUTTON
)
from web_agent_site.engine.goal import get_reward, get_goals
from web_agent_site.utils import (
    generate_order_code,
    setup_logger,
    DEFAULT_FILE_PATH,
    DEBUG_PROD_SIZE,
    BASE_DIR,
)

def _parse_args(argv):
    """Parse CLI args for theme selection and optional port override."""
    num_to_theme = {
        '1': 'webshop2000',
        '2': 'webshop2005',
        '3': 'webshop2010',
        '4': 'webshop2015',
        '5': 'webshop2025',
        '6': 'classic',
    }
    name_aliases = {
        'classic': 'classic',
        'webshop2000': 'webshop2000',
        'webshop2005': 'webshop2005',
        'webshop2010': 'webshop2010',
        'webshop2015': 'webshop2015',
        'webshop2025': 'webshop2025',
        'all': 'all',
    }
    selected_theme = 'classic'
    port_override = None
    run_all = False
    for raw in argv[1:]:
        arg = raw.lstrip('-').lower()
        if raw.startswith('--port='):
            try:
                port_override = int(raw.split('=', 1)[1])
            except Exception:
                pass
            continue
        if arg in num_to_theme:
            selected_theme = num_to_theme[arg]
        elif arg in name_aliases:
            if name_aliases[arg] == 'all':
                run_all = True
            else:
                selected_theme = name_aliases[arg]
    return selected_theme, port_override, run_all

# Determine theme and port from command line arguments
THEME, PORT_OVERRIDE, RUN_ALL = _parse_args(sys.argv)

print(f"Using theme: {THEME}")

# Initialize Flask with theme-specific paths
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'themes', THEME, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'themes', THEME, 'static'))

# Set theme in engine module
set_theme(THEME)

search_engine = None
all_products = None
product_item_dict = None
product_prices = None
attribute_to_asins = None
goals = None
weights = None

user_sessions = dict()
user_log_dir = None
SHOW_ATTRS_TAB = False

@app.route('/')
def home():
    return redirect(url_for('index', session_id="abc"))

@app.route('/<session_id>', methods=['GET', 'POST'])
def index(session_id):
    global user_log_dir
    global all_products, product_item_dict, \
           product_prices, attribute_to_asins, \
           search_engine, \
           goals, weights, user_sessions

    if search_engine is None:
        all_products, product_item_dict, product_prices, attribute_to_asins = \
            load_products(
                filepath=DEFAULT_FILE_PATH,
                num_products=DEBUG_PROD_SIZE
            )
        search_engine = init_search_engine(num_products=DEBUG_PROD_SIZE)
        goals = get_goals(all_products, product_prices)
        random.seed(233)
        random.shuffle(goals)
        weights = [goal['weight'] for goal in goals]

    if session_id not in user_sessions and 'fixed' in session_id:
        goal_dix = int(session_id.split('_')[-1])
        goal = goals[goal_dix]
        instruction_text = goal['instruction_text']
        user_sessions[session_id] = {'goal': goal, 'done': False}
        if user_log_dir is not None:
            setup_logger(session_id, user_log_dir)
    elif session_id not in user_sessions:
        goal = random.choices(goals, weights)[0]
        instruction_text = goal['instruction_text']
        user_sessions[session_id] = {'goal': goal, 'done': False}
        if user_log_dir is not None:
            setup_logger(session_id, user_log_dir)
    else:
        instruction_text = user_sessions[session_id]['goal']['instruction_text']

    if request.method == 'POST' and 'search_query' in request.form:
        keywords = request.form['search_query'].lower().split(' ')
        return redirect(url_for(
            'search_results',
            session_id=session_id,
            keywords=keywords,
            page=1,
        ))
    if user_log_dir is not None:
        logger = logging.getLogger(session_id)
        logger.info(json.dumps(dict(
            page='index',
            url=request.url,
            goal=user_sessions[session_id]['goal'],
        )))
    # Prepare a featured women's clothing item for summer collection hero
    featured_dress_asin = None
    featured_dress_title = None
    featured_dress_image = None
    try:
        # Try multiple search terms to find women's clothing - prioritize different types
        search_terms_list = [
            ['women', 'blouse'],
            ['women', 'top'],
            ['women', 'shirt'],
            ['women', 'skirt'],
            ['women', 'pants'],
            ['summer', 'dress'],
            ['women', 'dress'],
            ['dress'],
            ['women', 'fashion'],
            ['summer', 'clothing'],
            ['clothing', 'women'],
        ]
        # Try to get a different item each time by shuffling
        random.shuffle(search_terms_list)
        
        # Collect all candidates first, then pick a random one
        all_candidates = []
        for search_terms in search_terms_list:
            top_dress_asins = get_top_n_product_from_keywords(
                search_terms,
                search_engine,
                all_products,
                product_item_dict,
                attribute_to_asins,
            )
            if not top_dress_asins:
                continue
            # Get multiple candidates and collect them
            candidates = get_product_per_page(top_dress_asins, min(10, len(top_dress_asins))) or []
            for p in candidates:
                img = p.get('MainImage') or p.get('Image') or p.get('image')
                if img and isinstance(img, str) and img.strip() and 'no-image' not in img.lower():
                    all_candidates.append(p)
        
        # Pick a random candidate from all collected
        if all_candidates:
            random.shuffle(all_candidates)
            selected = all_candidates[0]
            featured_dress_asin = selected.get('asin')
            featured_dress_title = selected.get('Title') or 'Featured Item'
            featured_dress_image = selected.get('MainImage') or selected.get('Image') or selected.get('image')
        
        # If no image found, still try to use first product from any search
        if not featured_dress_asin and search_engine is not None:
            for search_terms in search_terms_list:
                top_dress_asins = get_top_n_product_from_keywords(
                    search_terms,
                    search_engine,
                    all_products,
                    product_item_dict,
                    attribute_to_asins,
                )
                if top_dress_asins:
                    candidates = get_product_per_page(top_dress_asins, 1) or []
                    if candidates:
                        featured_dress_asin = candidates[0].get('asin')
                        featured_dress_title = candidates[0].get('Title') or 'Featured Item'
                        # Try to get image from product_item_dict
                        if featured_dress_asin in product_item_dict:
                            img = product_item_dict[featured_dress_asin].get('MainImage') or product_item_dict[featured_dress_asin].get('Image')
                            if img and isinstance(img, str) and img.strip() and 'no-image' not in img.lower():
                                featured_dress_image = img
                        break
        # Fallback image (local placeholder)
        if not featured_dress_image:
            featured_dress_image = url_for('static', filename='images/no-image-available.png')
    except Exception as e:
        print(f"Error fetching featured clothing item: {e}")
        featured_dress_asin = None
        featured_dress_title = None
        featured_dress_image = url_for('static', filename='images/no-image-available.png')

    # Prepare featured products with images for bottom section
    featured_items = []
    if all_products and len(all_products) > 0:
        # Try to get products with images
        candidates = random.sample(all_products, min(30, len(all_products)))
        for prod in candidates:
            img = prod.get('MainImage') or prod.get('Image') or prod.get('image')
            if img and isinstance(img, str) and img.strip() and 'no-image' not in img.lower():
                featured_items.append(prod)
                if len(featured_items) >= 10:  # Get 10 featured items
                    break
        # If we don't have enough with images, fill with any products
        if len(featured_items) < 10:
            remaining = [p for p in all_products if p not in featured_items]
            featured_items.extend(remaining[:10 - len(featured_items)])

    # Get electronics product image for category background (cable, adapter, etc.)
    electronics_image = None
    try:
        electronics_search_terms = [
            ['cable'],
            ['bluetooth', 'adapter'],
            ['usb', 'cable'],
            ['car', 'stereo'],
            ['adapter'],
            ['electronics'],
        ]
        for search_terms in electronics_search_terms:
            electronics_products = get_top_n_product_from_keywords(
                search_terms,
                search_engine,
                all_products,
                product_item_dict,
                attribute_to_asins,
            )
            if not electronics_products:
                continue
            candidates = get_product_per_page(electronics_products, 1) or []
            for p in candidates:
                img = p.get('MainImage') or p.get('Image') or p.get('image')
                if img and isinstance(img, str) and img.strip() and 'no-image' not in img.lower():
                    electronics_image = img
                    break
            if electronics_image:
                break
    except Exception as e:
        print(f"Error fetching electronics image: {e}")
        electronics_image = None

    # Get featured products for right sidebar (homepage)
    featured_sidebar_products = None
    if all_products and len(all_products) > 0:
        # Get random products with images for the sidebar
        candidates = random.sample(all_products, min(10, len(all_products)))
        featured_sidebar_products = []
        for prod in candidates:
            img = prod.get('MainImage') or prod.get('Image') or prod.get('image')
            if img and isinstance(img, str) and img.strip() and 'no-image' not in img.lower():
                featured_sidebar_products.append(prod)
                if len(featured_sidebar_products) >= 4:  # Show 4 featured products
                    break
        # Fill with any products if we don't have enough with images
        if len(featured_sidebar_products) < 4:
            remaining = [p for p in all_products if p not in featured_sidebar_products]
            featured_sidebar_products.extend(remaining[:4 - len(featured_sidebar_products)])

    return map_action_to_html(
        'start',
        session_id=session_id,
        instruction_text=instruction_text,
        featured_products=featured_items[:4] if featured_items else None,
        featured_items=featured_items[:10] if featured_items else None,  # Up to 10 items for bottom section
        featured_dress_asin=featured_dress_asin,
        featured_dress_title=featured_dress_title,
        featured_dress_image=featured_dress_image,
        electronics_image=electronics_image,
        featured_sidebar_products=featured_sidebar_products[:4] if featured_sidebar_products else None,
    )


@app.route(
    '/search_results/<session_id>/<keywords>/<page>',
    methods=['GET', 'POST']
)
def search_results(session_id, keywords, page):
    instruction_text = user_sessions[session_id]['goal']['instruction_text']
    page = convert_web_app_string_to_var('page', page)
    keywords = convert_web_app_string_to_var('keywords', keywords)
    top_n_products = get_top_n_product_from_keywords(
        keywords,
        search_engine,
        all_products,
        product_item_dict,
        attribute_to_asins,
    )
    products = get_product_per_page(top_n_products, page)
    
    # Get featured products for right sidebar (2015 template only)
    featured_sidebar_products = None
    if all_products and len(all_products) > 0:
        # Get random products with images for the sidebar
        candidates = random.sample(all_products, min(10, len(all_products)))
        featured_sidebar_products = []
        for prod in candidates:
            img = prod.get('MainImage') or prod.get('Image') or prod.get('image')
            if img and isinstance(img, str) and img.strip() and 'no-image' not in img.lower():
                featured_sidebar_products.append(prod)
                if len(featured_sidebar_products) >= 4:  # Show 4 featured products
                    break
        # Fill with any products if we don't have enough with images
        if len(featured_sidebar_products) < 4:
            remaining = [p for p in all_products if p not in featured_sidebar_products]
            featured_sidebar_products.extend(remaining[:4 - len(featured_sidebar_products)])
    
    html = map_action_to_html(
        'search',
        session_id=session_id,
        products=products,
        keywords=keywords,
        page=page,
        total=len(top_n_products),
        instruction_text=instruction_text,
        featured_sidebar_products=featured_sidebar_products[:4] if featured_sidebar_products else None,
    )
    logger = logging.getLogger(session_id)
    logger.info(json.dumps(dict(
        page='search_results',
        url=request.url,
        goal=user_sessions[session_id]['goal'],
        content=dict(
            keywords=keywords,
            search_result_asins=[p['asin'] for p in products],
            page=page,
        )
    )))
    return html


@app.route(
    '/item_page/<session_id>/<asin>/<keywords>/<page>/<options>',
    methods=['GET', 'POST']
)
def item_page(session_id, asin, keywords, page, options):
    options = literal_eval(options)
    product_info = product_item_dict[asin]

    goal_instruction = user_sessions[session_id]['goal']['instruction_text']
    product_info['goal_instruction'] = goal_instruction

    html = map_action_to_html(
        'click',
        session_id=session_id,
        product_info=product_info,
        keywords=keywords,
        page=page,
        asin=asin,
        options=options,
        instruction_text=goal_instruction,
        show_attrs=SHOW_ATTRS_TAB,
    )
    logger = logging.getLogger(session_id)
    logger.info(json.dumps(dict(
        page='item_page',
        url=request.url,
        goal=user_sessions[session_id]['goal'],
        content=dict(
            keywords=keywords,
            page=page,
            asin=asin,
            options=options,
        )
    )))
    return html


@app.route(
    '/item_sub_page/<session_id>/<asin>/<keywords>/<page>/<sub_page>/<options>',
    methods=['GET', 'POST']
)
def item_sub_page(session_id, asin, keywords, page, sub_page, options):
    options = literal_eval(options)
    product_info = product_item_dict[asin]

    goal_instruction = user_sessions[session_id]['goal']['instruction_text']
    product_info['goal_instruction'] = goal_instruction

    html = map_action_to_html(
        f'click[{sub_page}]',
        session_id=session_id,
        product_info=product_info,
        keywords=keywords,
        page=page,
        asin=asin,
        options=options,
        instruction_text=goal_instruction
    )
    logger = logging.getLogger(session_id)
    logger.info(json.dumps(dict(
        page='item_sub_page',
        url=request.url,
        goal=user_sessions[session_id]['goal'],
        content=dict(
            keywords=keywords,
            page=page,
            asin=asin,
            options=options,
        )
    )))
    return html


@app.route('/done/<session_id>/<asin>/<options>', methods=['GET', 'POST'])
def done(session_id, asin, options):
    options = literal_eval(options)
    goal = user_sessions[session_id]['goal']
    purchased_product = product_item_dict[asin]
    price = product_prices[asin]

    reward, reward_info = get_reward(
        purchased_product,
        goal,
        price=price,
        options=options,
        verbose=True
    )
    user_sessions[session_id]['done'] = True
    user_sessions[session_id]['reward'] = reward
    print(user_sessions)

    logger = logging.getLogger(session_id)
    logger.info(json.dumps(dict(
        page='done',
        url=request.url,
        goal=goal,
        content=dict(
            asin=asin,
            options=options,
            price=price,
        ),
        reward=reward,
        reward_info=reward_info,
    )))
    del logging.root.manager.loggerDict[session_id]
    
    return map_action_to_html(
        f'click[{END_BUTTON}]',
        session_id=session_id,
        reward=reward,
        asin=asin,
        options=options,
        reward_info=reward_info,
        query=purchased_product['query'],
        category=purchased_product['category'],
        product_category=purchased_product['product_category'],
        goal_attrs=user_sessions[session_id]['goal']['attributes'],
        purchased_attrs=purchased_product['Attributes'],
        goal=goal,
        mturk_code=generate_order_code(asin, options),
    )


@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve shared assets from env/webshop/assets for use in templates."""
    assets_dir = os.path.normpath(os.path.join(BASE_DIR, '..', 'assets'))
    return send_from_directory(assets_dir, filename)

@app.route('/site_assets/<path:filename>')
def serve_site_assets(filename):
    """Serve assets located under env/webshop/web_agent_site/assets."""
    site_assets_dir = os.path.join(BASE_DIR, 'assets')
    return send_from_directory(site_assets_dir, filename)


def find_free_port(start_port=5000, max_attempts=100):
    """Find a free port starting from start_port"""
    for i in range(max_attempts):
        port = start_port + i
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('localhost', port))
            sock.close()
            return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find a free port in range {start_port}-{start_port + max_attempts}")

def find_free_ports(count=6, start_port=5000, max_attempts=100):
    """Find multiple sequential free ports starting from start_port"""
    ports = []
    current_port = start_port
    attempts = 0
    
    while len(ports) < count and attempts < max_attempts:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('localhost', current_port))
            sock.close()
            ports.append(current_port)
            current_port += 1
        except OSError:
            # Port is in use, try next port
            current_port += 1
        attempts += 1
    
    if len(ports) < count:
        raise RuntimeError(f"Could not find {count} free ports in range {start_port}-{start_port + max_attempts}")
    
    return ports

if __name__ == "__main__":
    import subprocess
    import time
    
    # Create parser - theme arguments are handled by _parse_args() at module level
    # so we use parse_known_args to ignore theme args
    parser = argparse.ArgumentParser(
        description="WebShop flask app backend configuration",
        allow_abbrev=False
    )
    parser.add_argument("--log", action='store_true', help="Log actions on WebShop in trajectory file")
    parser.add_argument("--attrs", action='store_true', help="Show attributes tab in item page")
    
    # parse_known_args will return (args, unknown) where unknown contains theme args
    args, unknown = parser.parse_known_args()
    if args.log:
        user_log_dir = Path('user_session_logs/mturk')
        user_log_dir.mkdir(parents=True, exist_ok=True)
    SHOW_ATTRS_TAB = args.attrs

    # If -all provided, spawn six servers (1-6) on successive ports
    if RUN_ALL:
        theme_nums = ['1', '2', '3', '4', '5', '6']
        procs = []
        # Get the parent directory (env/webshop) so Python can find web_agent_site module
        parent_dir = Path(__file__).parent.parent
        # Find sequential free ports in 5000 series
        if PORT_OVERRIDE:
            # If port override provided, start from that port and find sequential ports
            ports = find_free_ports(count=len(theme_nums), start_port=PORT_OVERRIDE)
        else:
            # Start from 5000 and find sequential free ports
            ports = find_free_ports(count=len(theme_nums), start_port=5000)
        print("\n" + "="*60)
        print("Starting multiple WebShop UI servers...")
        for i, num in enumerate(theme_nums):
            port = ports[i]
            # Run as module so Python can find web_agent_site package
            cmd = [sys.executable, "-m", "web_agent_site.app", num, f"--port={port}"]
            if args.log:
                cmd.append("--log")
            if args.attrs:
                cmd.append("--attrs")
            try:
                p = subprocess.Popen(cmd, cwd=str(parent_dir))
                procs.append((num, port, p.pid))
            except Exception as e:
                print(f"Failed to start server {num} on port {port}: {e}")
        for num, port, pid in procs:
            print(f"Server {num} running at http://localhost:{port} (PID {pid})")
        print("="*60 + "\n")
        # Keep parent alive to avoid abrupt exit; wait for children
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            pass
    else:
        # Determine port - use find_free_port to ensure it's actually free
        port = PORT_OVERRIDE if PORT_OVERRIDE else find_free_port()
        
        # Run the Flask app
        print("\n" + "="*60)
        print("WebShop UI is starting...")
        print(f"Using theme: {THEME}")
        print(f"Open your browser and go to: http://localhost:{port}")
        print("="*60 + "\n")
        
        app.run(host='0.0.0.0', port=port, use_reloader=False)
