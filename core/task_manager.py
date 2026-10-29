"""
Task Manager - Updated with:
- Two-phase flow: DISCOVER PHASE → URL SELECTION → SCRAPE PHASE
- User can select which URLs to scrape or scrape all
- Custom keyword support passed through to extractor
- discovered_candidates stored per task so UI can show them
"""

import threading
import time
from collections import deque
import re
from urllib.parse import urlparse
from core.extractor import BusinessLeadExtractor, COMMON_KEYWORD_TYPOS
from data.india_data import CONSTRUCTION_CATEGORIES, INDIAN_STATES_AND_DISTRICTS

class LeadExtractionManager:
    def __init__(self):
        self.lock = threading.RLock()
        self.thread = None
        self.status = "idle"  # idle, discovering, awaiting_selection, running, paused, stopped, completed
        self.should_abort = False
        self.is_paused = False

        # Task state
        self.tasks = []
        self.current_task_index = 0
        self.current_task_info = ""
        self.current_site_info = ""
        self.total_child_pages = 0

        # Discovery phase
        self.discovered_candidates = []   # flat list of all discovered URLs across tasks
        self.selected_urls = set()        # URLs user selected to scrape
        self.scrape_all_mode = False      # True = scrape all discovered, False = use selected_urls

        self.leads = []
        self.logs = deque(maxlen=500)

        self.current_scrape_index = 0
        self.total_scrape_count = 0

        # Auto Processing state
        self.is_auto_mode = False
        self.is_pan_india = False
        self.latest_master_file = ""
        self.latest_master_url = ""
        self.exported_district_files = []

        self.start_time = None
        self.completed_time = None

    def add_log(self, message, level='info'):
        timestamp = time.strftime("%H:%M:%S")
        with self.lock:
            self.logs.append({"timestamp": timestamp, "message": message, "level": level})

    def get_status(self):
        with self.lock:
            total_tasks = len(self.tasks)
            completed_tasks = self.current_task_index
            total_leads = len(self.leads)
            with_phone = sum(1 for l in self.leads if l.get('mobile_numbers') or l.get('office_numbers'))
            with_email = sum(1 for l in self.leads if l.get('email_addresses'))
            elapsed = 0
            if self.start_time:
                end = self.completed_time or time.time()
                elapsed = int(end - self.start_time)

            if self.status == "completed":
                prog = 100
            elif self.is_auto_mode and total_tasks > 0:
                dist_prog = (completed_tasks / total_tasks) * 100
                inner = ((self.current_scrape_index / self.total_scrape_count) * (100 / total_tasks)) if self.total_scrape_count > 0 else 0
                prog = min(99, int(dist_prog + inner))
            elif self.status == "running" and self.total_scrape_count > 0:
                prog = int((self.current_scrape_index / self.total_scrape_count) * 100)
            elif total_tasks > 0:
                prog = int((completed_tasks / total_tasks) * 100)
            else:
                prog = 0

            return {
                "status": self.status,
                "is_auto_mode": self.is_auto_mode,
                "is_pan_india": self.is_pan_india,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "progress_percent": prog,
                "current_task": self.current_task_info,
                "current_site": self.current_site_info,
                "total_child_pages": self.total_child_pages,
                "total_leads": total_leads,
                "leads_with_phone": with_phone,
                "leads_with_email": with_email,
                "elapsed_seconds": elapsed,
                "recent_logs": list(self.logs)[-30:],
                "discovered_count": len(self.discovered_candidates),
                "latest_master_file": self.latest_master_file,
                "latest_master_url": self.latest_master_url,
                "exported_district_files": list(self.exported_district_files)
            }

    def get_leads(self):
        with self.lock:
            return list(self.leads)

    def get_discovered(self):
        with self.lock:
            return list(self.discovered_candidates)

    # ── PHASE 1: DISCOVER URLS ──────────────────────────────────────────────────
    def start_discovery(self, selected_states, selected_districts, selected_categories,
                        custom_location="", custom_keyword="", search_engines=None):
        with self.lock:
            if self.status in ["running", "discovering"]:
                return False, "An extraction or discovery is already in progress."

            self.tasks = []
            self.current_task_index = 0
            self.current_task_info = ""
            self.current_site_info = ""
            self.total_child_pages = 0
            self.leads = []
            self.logs.clear()
            self.discovered_candidates = []
            self.selected_urls = set()
            self.should_abort = False
            self.is_paused = False
            self.status = "discovering"
            self.start_time = time.time()
            self.completed_time = None

        # Build tasks
        custom_kw = custom_keyword.strip()
        if custom_kw:
            # Custom Search Keyword overrides default categories to strictly target that exact business type
            kw_lower = custom_kw.lower()
            words = re.split(r'(\W+)', kw_lower)
            kw_norm = ''.join(COMMON_KEYWORD_TYPOS.get(w, w) for w in words)
            kw_terms = [kw_lower, kw_norm]
            if 'steel' in kw_norm:
                kw_terms.extend(['steel', 'steels', 'tmt', 'iron & steel', 'steel trader', 'steel mart'])
            elif 'metal' in kw_norm:
                kw_terms.extend(['metal', 'metals', 'sheet metal', 'metal mart', 'scrap metal'])
            else:
                for w in kw_norm.split():
                    if len(w) >= 2:
                        kw_terms.append(w)
            search_terms = [custom_kw]
            if kw_norm != kw_lower:
                search_terms.append(kw_norm)
            target_cats = [{
                "id": "custom_search",
                "name": custom_kw.title(),
                "keywords": list(set(kw_terms)),
                "search_terms": search_terms
            }]
        else:
            categories_dict = {cat['id']: cat for cat in CONSTRUCTION_CATEGORIES}
            target_cats = [categories_dict[cid] for cid in selected_categories if cid in categories_dict]
            if not target_cats:
                target_cats = [CONSTRUCTION_CATEGORIES[0]]

        # Strict A to Z alphabetical ordering for states & districts + Zero duplicate districts
        sorted_states = sorted(list(set(selected_states)))
        tasks = []
        seen_state_districts = set()

        for state in sorted_states:
            districts_in_state = INDIAN_STATES_AND_DISTRICTS.get(state, [])
            dist_pool = [d for d in districts_in_state if d in selected_districts] if selected_districts else districts_in_state
            sorted_districts = sorted(list(set(dist_pool)))
            for dist in sorted_districts:
                norm_key = (state.strip().lower(), dist.strip().lower())
                if norm_key in seen_state_districts:
                    continue
                seen_state_districts.add(norm_key)
                for cat in target_cats:
                    tasks.append({
                        "state": state,
                        "district": dist,
                        "city": custom_location.strip(),
                        "custom_keyword": custom_keyword.strip(),
                        "category": cat,
                        "search_engines": search_engines
                    })

        if not tasks:
            with self.lock:
                self.status = "idle"
            return False, "No valid tasks generated."

        with self.lock:
            self.tasks = tasks

        self.add_log(f"Starting URL discovery for {len(tasks)} task(s)...", 'info')

        self.thread = threading.Thread(target=self._run_discovery, daemon=True)
        self.thread.start()
        return True, f"Discovery started for {len(tasks)} task(s)."

    def _run_discovery(self):
        extractor = BusinessLeadExtractor(
            log_callback=self.add_log,
            check_abort=lambda: self.should_abort,
            check_pause=lambda: self.is_paused
        )
        self.active_extractor = extractor

        all_candidates = []
        seen_urls = set()

        for i, task in enumerate(self.tasks):
            if self.should_abort:
                break

            with self.lock:
                self.current_task_index = i
                loc = f"{task['city']}, " if task['city'] else ""
                self.current_task_info = f"Discovering: {loc}{task['district']} ({task['state']}) — {task['category']['name']}"

            self.add_log(f"[{i+1}/{len(self.tasks)}] {self.current_task_info}", 'info')

            candidates = extractor.discover_candidates(
                state=task['state'],
                district=task['district'],
                city=task['city'],
                category_item=task['category'],
                custom_keyword=task.get('custom_keyword', ''),
                search_engines=task.get('search_engines')
            )

            for cand in candidates:
                url = cand['url']
                if url not in seen_urls:
                    seen_urls.add(url)
                    # Tag with task info
                    cand['task_state'] = task['state']
                    cand['task_district'] = task['district']
                    cand['task_city'] = task['city']
                    cand['task_category'] = task['category']['id']
                    cand['task_category_name'] = task['category']['name']
                    cand['task_category_item'] = task['category']
                    cand['task_custom_keyword'] = task.get('custom_keyword', '')
                    all_candidates.append(cand)

            self.add_log(f"Found {len(candidates)} URLs for {task['district']}.", 'info')

        with self.lock:
            self.discovered_candidates = all_candidates
            if not self.should_abort:
                self.status = "awaiting_selection"
                self.add_log(
                    f"Discovery complete! {len(all_candidates)} URLs found. "
                    f"Select URLs to scrape or click 'Scrape All'.", 'success'
                )
            else:
                self.status = "stopped"
                self.completed_time = time.time()

    # ── PHASE 2: SCRAPE SELECTED / ALL ─────────────────────────────────────────
    def start_scraping(self, selected_urls=None):
        """
        Begin scraping phase.
        selected_urls: list of URLs to scrape. None / empty = scrape all discovered.
        """
        with self.lock:
            if self.status not in ["awaiting_selection", "stopped", "completed"]:
                return False, "Run discovery first."
            if not self.discovered_candidates:
                return False, "No discovered URLs to scrape."

            if selected_urls:
                self.selected_urls = set(selected_urls)
                self.scrape_all_mode = False
            else:
                self.selected_urls = set()
                self.scrape_all_mode = True

            self.should_abort = False
            self.is_paused = False
            self.status = "running"
            self.current_site_info = ""
            self.start_time = self.start_time or time.time()
            self.completed_time = None

        n = len(self.selected_urls) if not self.scrape_all_mode else len(self.discovered_candidates)
        self.add_log(f"Starting scraping of {n} URL(s)...", 'info')

        self.thread = threading.Thread(target=self._run_scraping, daemon=True)
        self.thread.start()
        return True, f"Scraping started for {n} URL(s)."

    def _add_lead_safe(self, lead):
        if not lead:
            return
        items = lead if isinstance(lead, list) else [lead]
        loc_checker = BusinessLeadExtractor()
        with self.lock:
            existing_keys = {
                (
                    l.get('business_name', '').strip().lower(),
                    l.get('mobile_numbers', '').strip(),
                    l.get('district', '').strip().lower(),
                    urlparse(l.get('source_url', '')).netloc.lower().replace('www.', '')
                )
                for l in self.leads
            }
            for item in items:
                b_name = item.get('business_name', '').strip().lower()
                b_phone = item.get('mobile_numbers', '').strip()
                src_domain = urlparse(item.get('source_url', '')).netloc.lower().replace('www.', '')
                dist = item.get('district', '')
                st = item.get('state', '')
                city = item.get('city_area', '')
                check_str = f"{item.get('business_name', '')} {item.get('address', '')}"
                if dist and loc_checker.has_conflicting_location(check_str, dist, st, city if city != dist else None):
                    continue
                # Strict Category Relevance & Unrelated Industry Filter (Ultimate Guardrail)
                raw_bname = item.get('business_name', '').strip()
                cat_obj = item.get('task_category_item')
                kw_val = item.get('task_custom_keyword', '')
                is_rel, rel_reason = loc_checker.is_strictly_category_relevant(
                    raw_bname, f"{raw_bname} {item.get('address','')} {item.get('category','')}", cat_obj, kw_val
                )
                if not is_rel:
                    continue
                key = (b_name, b_phone, dist.strip().lower(), src_domain)
                if key not in existing_keys and b_name:
                    existing_keys.add(key)
                    self.leads.append(item)
                    self.total_child_pages += item.get('child_pages_crawled', 0)

    def _run_scraping(self):
        try:
            extractor = BusinessLeadExtractor(
                log_callback=self.add_log,
                check_abort=lambda: self.should_abort,
                check_pause=lambda: self.is_paused,
                lead_callback=self._add_lead_safe
            )
            self.active_extractor = extractor

            # Restore dedup state from already-extracted leads
            for lead in self.leads:
                src_domain = urlparse(lead.get('source_url', '')).netloc.lower().replace('www.', '')
                for ph in lead.get('mobile_numbers', '').split(','):
                    ph = ph.strip()
                    if ph:
                        extractor.seen_phones.add((src_domain, ph))
                for em in lead.get('email_addresses', '').split(','):
                    em = em.strip()
                    if em:
                        extractor.seen_emails.add((src_domain, em))
                domain = lead.get('website', '').replace('https://', '').replace('http://', '').split('/')[0].lower()
                if domain and not extractor.is_directory_domain(domain):
                    extractor.seen_domains.add(domain)

            candidates_to_scrape = [
                c for c in self.discovered_candidates
                if self.scrape_all_mode or c['url'] in self.selected_urls
            ]

            with self.lock:
                self.total_scrape_count = len(candidates_to_scrape)
                self.current_scrape_index = 0

            # Match task category info back to each candidate
            cat_map = {cat['id']: cat for cat in CONSTRUCTION_CATEGORIES}

            for idx, cand in enumerate(candidates_to_scrape):
                if self.should_abort:
                    break

                while self.is_paused and not self.should_abort:
                    time.sleep(0.5)

                with self.lock:
                    self.current_scrape_index = idx + 1
                    self.current_site_info = cand.get('url', '')
                    self.current_task_info = (
                        f"Scraping [{idx+1}/{len(candidates_to_scrape)}]: "
                        f"{cand.get('task_district','')} — {cand.get('task_category_name','')}"
                    )

                cat_id = cand.get('task_category', 'civil_contractors')
                cat_item = cand.get('task_category_item') or cat_map.get(cat_id, CONSTRUCTION_CATEGORIES[0])

                try:
                    lead = extractor.scrape_business_site(
                        candidate=cand,
                        category_item=cat_item,
                        state=cand.get('task_state', ''),
                        district=cand.get('task_district', ''),
                        city=cand.get('task_city', ''),
                        custom_keyword=cand.get('task_custom_keyword', '')
                    )

                    if lead:
                        self._add_lead_safe(lead)
                except Exception as ex:
                    self.add_log(f"Error scraping {cand.get('url')}: {ex}", 'debug')

                time.sleep(0.5)

            with self.lock:
                if not self.should_abort:
                    self.status = "completed"
                    self.current_task_index = len(self.tasks)
                    self.completed_time = time.time()
                    self.add_log(
                        f"Scraping complete! Total verified leads: {len(self.leads)}", 'success'
                    )
                else:
                    self.status = "stopped"
                    self.completed_time = time.time()

        except Exception as e:
            self.add_log(f"Scraper error: {e}", 'error')
            with self.lock:
                self.status = "stopped"
                self.completed_time = time.time()

    # ── CONTROLS ────────────────────────────────────────────────────────────────
    def pause_extraction(self):
        with self.lock:
            if self.status in ["running", "discovering"]:
                self.is_paused = True
                self.status = "paused"
                self.add_log("Paused by user.", 'warning')
                return True, "Paused."
            return False, "Not currently running."

    def resume_extraction(self):
        with self.lock:
            if self.status == "paused":
                self.is_paused = False
                self.status = "running"
                self.add_log("Resumed.", 'info')
                return True, "Resumed."
            return False, "Not paused."

    def stop_extraction(self):
        with self.lock:
            if self.status in ["running", "paused", "discovering"]:
                self.should_abort = True
                self.is_paused = False
                self.status = "stopped"
                self.completed_time = time.time()
                if hasattr(self, 'active_extractor') and self.active_extractor:
                    try:
                        self.active_extractor.abort()
                    except Exception:
                        pass
                self.add_log("🛑 Stopped extraction instantly. Finalizing verified leads export...", 'warning')
                return True, "Stopped."
            return False, "Not active."

    def clear_results(self):
        with self.lock:
            if self.status in ["running", "paused", "discovering"]:
                return False, "Cannot clear while running. Stop first."
            self.tasks = []
            self.current_task_index = 0
            self.current_task_info = ""
            self.current_site_info = ""
            self.total_child_pages = 0
            self.leads = []
            self.logs.clear()
            self.discovered_candidates = []
            self.selected_urls = set()
            self.current_scrape_index = 0
            self.total_scrape_count = 0
            self.is_auto_mode = False
            self.is_pan_india = False
            self.latest_master_file = ""
            self.latest_master_url = ""
            self.exported_district_files = []
            self.status = "idle"
            self.start_time = None
            self.completed_time = None
            return True, "Cleared."

    # ── FULL AUTO PROCESSING (DISCOVER + SCRAPE + DISTRICT EXPORT + MASTER EXPORT) ───
    def start_auto_processing(self, selected_states, selected_districts, selected_categories,
                              custom_location="", custom_keyword="", search_engines=None,
                              is_pan_india=False):
        with self.lock:
            if self.status in ["running", "discovering"]:
                return False, "An extraction or auto-processing is already in progress."

            self.tasks = []
            self.current_task_index = 0
            self.current_task_info = ""
            self.current_site_info = ""
            self.total_child_pages = 0
            self.leads = []
            self.logs.clear()
            self.discovered_candidates = []
            self.selected_urls = set()
            self.current_scrape_index = 0
            self.total_scrape_count = 0
            self.should_abort = False
            self.is_paused = False
            self.is_auto_mode = True
            self.is_pan_india = is_pan_india
            self.status = "running"
            self.latest_master_file = ""
            self.latest_master_url = ""
            self.exported_district_files = []
            self.start_time = time.time()
            self.completed_time = None

        # Ensure Google Search Engine is always selected in Auto Mode
        if search_engines is None:
            search_engines = ['google', 'brave']
        elif 'google' not in search_engines:
            search_engines = ['google'] + [e for e in search_engines if e != 'google']

        # Build tasks
        custom_kw = custom_keyword.strip()
        if custom_kw:
            kw_lower = custom_kw.lower()
            words = re.split(r'(\W+)', kw_lower)
            kw_norm = ''.join(COMMON_KEYWORD_TYPOS.get(w, w) for w in words)
            kw_terms = [kw_lower, kw_norm]
            if 'steel' in kw_norm:
                kw_terms.extend(['steel', 'steels', 'tmt', 'iron & steel', 'steel trader', 'steel mart'])
            elif 'metal' in kw_norm:
                kw_terms.extend(['metal', 'metals', 'sheet metal', 'metal mart', 'scrap metal'])
            else:
                for w in kw_norm.split():
                    if len(w) >= 2:
                        kw_terms.append(w)
            search_terms = [custom_kw]
            if kw_norm != kw_lower:
                search_terms.append(kw_norm)
            target_cats = [{
                "id": "custom_search",
                "name": custom_kw.title(),
                "keywords": list(set(kw_terms)),
                "search_terms": search_terms
            }]
        else:
            categories_dict = {cat['id']: cat for cat in CONSTRUCTION_CATEGORIES}
            target_cats = [categories_dict[cid] for cid in selected_categories if cid in categories_dict]
            if not target_cats:
                target_cats = [CONSTRUCTION_CATEGORIES[0]]

        if is_pan_india or (len(selected_states) >= len(INDIAN_STATES_AND_DISTRICTS)):
            sorted_states = sorted(list(INDIAN_STATES_AND_DISTRICTS.keys()))
            self.is_pan_india = True
        else:
            sorted_states = sorted(list(set(selected_states)))

        tasks = []
        seen_state_districts = set()

        for state in sorted_states:
            districts_in_state = INDIAN_STATES_AND_DISTRICTS.get(state, [])
            if self.is_pan_india or not selected_districts:
                dist_pool = districts_in_state
            else:
                dist_pool = [d for d in districts_in_state if d in selected_districts]

            # Strict A to Z alphabetical ordering for districts
            sorted_districts = sorted(list(set(dist_pool)))

            for dist in sorted_districts:
                norm_key = (state.strip().lower(), dist.strip().lower())
                # Zero duplicate districts across session
                if norm_key in seen_state_districts:
                    continue
                seen_state_districts.add(norm_key)

                for cat in target_cats:
                    tasks.append({
                        "state": state,
                        "district": dist,
                        "city": custom_location.strip(),
                        "custom_keyword": custom_keyword.strip(),
                        "category": cat,
                        "search_engines": search_engines
                    })

        if not tasks:
            with self.lock:
                self.status = "idle"
                self.is_auto_mode = False
                self.is_pan_india = False
            return False, "No valid district tasks generated."

        with self.lock:
            self.tasks = tasks

        if self.is_pan_india:
            self.add_log(f"🇮🇳 [PAN-INDIA AUTO-PILOT INITIALIZED] Starting A-to-Z automated extraction for {len(sorted_states)} States & {len(tasks)} unique District task(s)...", 'info')
        else:
            self.add_log(f"⚡ [A-TO-Z AUTO-PILOT INITIALIZED] Starting automated extraction for {len(tasks)} district task(s) in strict A-to-Z alphabetical order...", 'info')

        self.thread = threading.Thread(target=self._run_auto_processing, daemon=True)
        self.thread.start()
        return True, f"Auto-processing started for {len(tasks)} district task(s)."

    def _run_auto_processing(self):
        try:
            import os
            from core.exporter import generate_excel_export, generate_csv_export

            backend_exports_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend', 'exports'
            )
            os.makedirs(backend_exports_dir, exist_ok=True)

            total_dist_tasks = len(self.tasks)
            state_name = self.tasks[0]['state'] if self.tasks else "Tamil Nadu"

            for task_idx, task in enumerate(self.tasks):
                if self.should_abort:
                    break

                dist = task['district']
                st = task['state']
                cat = task['category']
                cat_name = cat['name']
                custom_kw = task.get('custom_keyword', '')
                engines = task.get('search_engines') or ['google', 'brave']

                # Solution 1: Fresh Isolated Extractor Instance per District
                # Resets seen_domains, seen_phones, session cookies, and Google Places cache
                # so that one district's leads never block or pollute another district
                extractor = BusinessLeadExtractor(
                    log_callback=self.add_log,
                    check_abort=lambda: self.should_abort,
                    check_pause=lambda: self.is_paused,
                    lead_callback=self._add_lead_safe
                )
                self.active_extractor = extractor

                with self.lock:
                    self.current_task_index = task_idx
                    self.current_task_info = f"⚡ Auto Processing [{task_idx+1}/{total_dist_tasks}]: {dist} ({st}) — {cat_name}"

                self.add_log(f"[{task_idx+1}/{total_dist_tasks}] Auto-Discovering leads in {dist}...", 'info')

                # Step 1: Discover URLs for this district
                dist_candidates = extractor.discover_candidates(
                    state=st,
                    district=dist,
                    city=task.get('city', ''),
                    category_item=cat,
                    custom_keyword=custom_kw,
                    search_engines=engines
                )

                for cand in dist_candidates:
                    cand['task_state'] = st
                    cand['task_district'] = dist
                    cand['task_city'] = task.get('city', '')
                    cand['task_category'] = cat['id']
                    cand['task_category_name'] = cat_name
                    cand['task_category_item'] = cat
                    cand['task_custom_keyword'] = custom_kw

                with self.lock:
                    self.discovered_candidates.extend(dist_candidates)

                self.add_log(f"Discovered {len(dist_candidates)} targets for {dist}. Now Auto-Scraping...", 'info')

                if self.should_abort:
                    break

                # Step 2: Auto-Scrape all candidates for this district
                with self.lock:
                    self.total_scrape_count = len(dist_candidates)
                    self.current_scrape_index = 0

                for s_idx, cand in enumerate(dist_candidates):
                    if self.should_abort:
                        break
                    while self.is_paused and not self.should_abort:
                        time.sleep(0.5)

                    with self.lock:
                        self.current_scrape_index = s_idx + 1
                        self.current_site_info = cand.get('url', '')

                    try:
                        lead = extractor.scrape_business_site(
                            candidate=cand,
                            category_item=cat,
                            state=st,
                            district=dist,
                            city=task.get('city', ''),
                            custom_keyword=custom_kw
                        )
                        if lead:
                            self._add_lead_safe(lead)
                    except Exception as ex:
                        self.add_log(f"Scrape note {cand.get('url')}: {ex}", 'debug')

                    for _ in range(4):
                        if self.should_abort:
                            break
                        time.sleep(0.1)

                # Step 2.5: Zero-Drop District Guarantee Recovery
                # If zero leads were obtained for this district (e.g. search engine throttling / rate-limit),
                # immediately scrape guaranteed direct directory targets (Justdial, IndiaMART, Sulekha, TradeIndia)
                with self.lock:
                    dist_leads = [
                        l for l in self.leads
                        if l.get('district', '').strip().lower() == dist.strip().lower()
                    ]

                if not dist_leads and not self.should_abort:
                    self.add_log(f"🔄 [ZERO-DROP GUARANTEE] Recovering direct verified directory leads for '{dist}'...", 'info')
                    recovery_seeds = extractor.generate_guaranteed_directory_seeds(
                        state=st,
                        district=dist,
                        city=task.get('city', ''),
                        category_item=cat,
                        custom_keyword=custom_kw
                    )
                    for r_cand in recovery_seeds:
                        if self.should_abort:
                            break
                        r_cand['task_state'] = st
                        r_cand['task_district'] = dist
                        r_cand['task_city'] = task.get('city', '')
                        r_cand['task_category'] = cat['id']
                        r_cand['task_category_name'] = cat_name
                        r_cand['task_category_item'] = cat
                        r_cand['task_custom_keyword'] = custom_kw

                        try:
                            lead = extractor.scrape_business_site(
                                candidate=r_cand,
                                category_item=cat,
                                state=st,
                                district=dist,
                                city=task.get('city', ''),
                                custom_keyword=custom_kw
                            )
                            if lead:
                                self._add_lead_safe(lead)
                        except Exception as ex:
                            self.add_log(f"Recovery scrape note ({r_cand.get('url')}): {ex}", 'debug')
                        for _ in range(3):
                            if self.should_abort:
                                break
                            time.sleep(0.1)

                # Step 3: Auto-Export this District's verified leads to backend/exports/ folder
                with self.lock:
                    dist_leads = [
                        l for l in self.leads
                        if l.get('district', '').strip().lower() == dist.strip().lower()
                    ]

                if dist_leads:
                    safe_dist = re.sub(r'\W+', '_', dist).strip('_')
                    safe_state = re.sub(r'\W+', '_', st).strip('_')
                    safe_cat = re.sub(r'\W+', '_', custom_kw or cat_name).strip('_')
                    ts = time.strftime("%Y%m%d_%H%M%S")
                    dist_filename = f"{safe_state}_{safe_dist}_{safe_cat}_{ts}.xlsx"
                    dist_filepath = os.path.join(backend_exports_dir, dist_filename)

                    try:
                        generate_excel_export(dist_leads, dist_filepath)
                        csv_filename = f"{safe_state}_{safe_dist}_{safe_cat}_{ts}.csv"
                        generate_csv_export(dist_leads, os.path.join(backend_exports_dir, csv_filename))

                        with self.lock:
                            self.exported_district_files.append({
                                "district": dist,
                                "filename": dist_filename,
                                "filepath": dist_filepath,
                                "leads_count": len(dist_leads),
                                "download_url": f"/api/export/file/{dist_filename}"
                            })

                        self.add_log(
                            f"💾 [AUTO-EXPORT SAVED] District '{dist}': {len(dist_leads)} verified leads saved to backend/exports/{dist_filename}",
                            'success'
                        )
                    except Exception as exp_err:
                        self.add_log(f"Auto-export error for {dist}: {exp_err}", 'error')
                else:
                    self.add_log(f"District '{dist}' completed. No verified leads found.", 'warning')

                if self.should_abort:
                    break

                # Close this district's extractor session cleanly
                try:
                    extractor.session.close()
                except Exception:
                    pass

                # Solution 2: Inter-District Cooldown Delay (Anti-Rate-Limiting Protection)
                # Adds a protective 10-second cool-off period so search engines and directories do not rate-limit
                if task_idx < total_dist_tasks - 1 and not self.should_abort:
                    next_task = self.tasks[task_idx + 1]
                    next_dist = next_task.get('district', '')
                    self.add_log(
                        f"⏳ [ANTI-BOT COOLDOWN] Completed '{dist}'. Cooling down 10s before starting next district '{next_dist}' ({task_idx+2}/{total_dist_tasks})...",
                        'info'
                    )
                    # Responsive 100ms interval sleep so user can click Stop anytime within <1s
                    for _ in range(100):
                        if self.should_abort:
                            break
                        time.sleep(0.1)

            # Step 4: Consolidate ALL collected leads across the State/Country into SINGLE MASTER EXCEL!
            if self.leads:
                unique_states = sorted(list(set(t['state'] for t in self.tasks if t.get('state'))))
                ts = time.strftime("%Y%m%d_%H%M%S")
                if len(unique_states) > 1 or self.is_pan_india:
                    master_filename = f"PAN_INDIA_MASTER_ALL_STATES_{ts}.xlsx"
                    master_csv = f"PAN_INDIA_MASTER_ALL_STATES_{ts}.csv"
                    log_text = f"🏆 [AUTO-EXPORT COMPLETE] Pan-India Master Excel generated: {master_filename} with {len(self.leads)} verified leads across {len(unique_states)} States!"
                else:
                    safe_state = re.sub(r'\W+', '_', unique_states[0] if unique_states else state_name).strip('_')
                    master_filename = f"{safe_state}_STATE_MASTER_ALL_DISTRICTS_{ts}.xlsx"
                    master_csv = f"{safe_state}_STATE_MASTER_ALL_DISTRICTS_{ts}.csv"
                    log_text = f"🏆 [AUTO-EXPORT COMPLETE] Master State Excel generated: {master_filename} with {len(self.leads)} verified leads across all districts!"

                master_filepath = os.path.join(backend_exports_dir, master_filename)

                try:
                    generate_excel_export(self.leads, master_filepath)
                    generate_csv_export(self.leads, os.path.join(backend_exports_dir, master_csv))

                    with self.lock:
                        self.latest_master_file = master_filename
                        self.latest_master_url = f"/api/export/file/{master_filename}"
                        self.status = "completed" if not self.should_abort else "stopped"
                        self.current_task_index = len(self.tasks)
                        self.completed_time = time.time()

                    if self.should_abort:
                        self.add_log(f"⏹️ Extraction stopped by user. {len(self.leads)} verified leads saved to {master_filename}", 'warning')
                    else:
                        self.add_log(log_text, 'success')
                except Exception as m_err:
                    self.add_log(f"Master file export error: {m_err}", 'error')
                    with self.lock:
                        self.status = "completed" if not self.should_abort else "stopped"
                        self.completed_time = time.time()
            else:
                with self.lock:
                    self.status = "completed" if not self.should_abort else "stopped"
                    self.current_task_index = len(self.tasks)
                    self.completed_time = time.time()
                if self.should_abort:
                    self.add_log("⏹️ Extraction stopped by user.", 'warning')

        except Exception as top_err:
            self.add_log(f"Auto-processing error: {top_err}", 'error')
            with self.lock:
                self.status = "stopped"
                self.completed_time = time.time()

    # Legacy compat — direct start without discovery phase
    def start_extraction(self, selected_states, selected_districts, selected_categories,
                         custom_location="", custom_keyword=""):
        return self.start_discovery(
            selected_states, selected_districts, selected_categories,
            custom_location, custom_keyword
        )
