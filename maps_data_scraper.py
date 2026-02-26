# -*- coding: utf-8 -*-

import random
import time
import re
import urllib.request
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from place_maps import MapsPlace


class GoogleMapsDataScraper:

    def __init__(self, language, img_output):
        self.driver = None
        self.error_count = 0
        self.img_output = img_output
        self.config = self._setup_config(language)

    def _setup_config(self, language):
        config = {
            'language': '--lang=es-ES',
            'stars_text': 'estrellas',
            'reviews_text': 'reseñas',
            'address_text': 'Dirección: ',
            'website_text': 'Sitio web: ',
            'phone_text': 'Teléfono: ',
            'pluscode_text': 'Plus Code: ',
            'hours_text': 'Ocultar el horario de la semana',
            'hours_replace': [' Ocultar el horario de la semana', 'El horario podría cambiar', '; '],
            'sort_text': 'Ordenar',
            'newest_text': 'Más recientes'
        }
        if language == 'EN':
            config['language'] = '--lang=en-GB'
            config['stars_text'] = 'stars'
            config['reviews_text'] = 'reviews'
            config['address_text'] = 'Address: '
            config['website_text'] = 'Website: '
            config['phone_text'] = 'Phone: '
            config['pluscode_text'] = 'Plus code: '
            config['hours_text'] = 'Hide open hours for the week'
            config['hours_replace'] = ['. Hide open hours for the week', 'Hours might differ', '; ']
            config['sort_text'] = 'Sort'
            config['newest_text'] = 'Newest'

        return config

    def init_driver(self):
        try:
            chrome_options = webdriver.ChromeOptions()
            #chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_argument(self.config['language'])
            s = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=s, options=chrome_options)
            self.driver.get('https://www.google.com/maps/')
            time.sleep(5)
            self.dismiss_popups()
            print("Page title:", self.driver.title)
            print("Current URL:", self.driver.current_url)
            return True
        except Exception as e:
            print(e)
            print('Error with the Chrome Driver')
            return False

    def dismiss_popups(self):
        """Dismiss any popups that might be blocking the search box."""
        try:
            btn = self.driver.find_element(By.XPATH, '//*[@aria-label="Accept all"]')
            btn.click()
            time.sleep(1)
        except:
            pass
        try:
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(0.5)
        except:
            pass

    def remove_accents(self, s):
        replacements = (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"),)
        for a, b in replacements:
            s = s.replace(a, b).replace(a.upper(), b.upper())
        return s

    def scrape_place(self, kw):
        try:
            place = MapsPlace()
            place.keyword = kw
            if self.error_count == 5:
                self.error_count = 0
                time.sleep(1)
                self.driver.get('https://www.google.com/maps/')
                time.sleep(3)
                self.dismiss_popups()

            time.sleep(random.randint(1, 3))
            self.dismiss_popups()
            time.sleep(1)

            # --- SEARCH ---
            try:
                input_box = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[name="q"]'))
                )
                print("[DEBUG] Found search box")
            except Exception as e:
                print(f"[DEBUG] Failed to find search box: {e}")
                return None

            input_box.click()
            time.sleep(0.5)
            input_box.clear()
            time.sleep(0.3)
            input_box.send_keys(kw)
            print(f"[DEBUG] Typed keyword: {kw}")
            time.sleep(1)
            input_box.send_keys(Keys.ENTER)
            print("[DEBUG] Pressed Enter")
            time.sleep(5)

            self.driver.save_screenshot('debug_after_search.png')
            print(f"[DEBUG] URL after search: {self.driver.current_url}")

            # --- CHECK IF RESULTS LOADED ---
            results = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="article"]')
            print(f"[DEBUG] Found {len(results)} results")

            if len(results) == 0:
                # No results list — maybe it opened a single place directly
                try:
                    titles = self.driver.find_elements(By.TAG_NAME, 'h1')
                    for t in titles:
                        if t.text.strip() != '' and t.text.strip() != 'Results':
                            place.name = t.text.strip()
                            print(f"[DEBUG] Single place opened: {place.name}")
                            break
                    else:
                        print("[DEBUG] No results and no place title found")
                        return None
                except:
                    print("[DEBUG] No results found at all")
                    return None
            else:
                # Get the place name from the aria-label of the first result
                place.name = results[0].get_attribute('aria-label')
                print(f"[DEBUG] Clicking first result: {place.name}")
                results[0].click()
                time.sleep(3)
                self.driver.save_screenshot('debug_after_click.png')

            time.sleep(1)

            # Stars and reviews
            try:
                val = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[contains(@aria-label, "' +
                                                                                          self.config['stars_text'] + '") and @role="img"]')))
                if '(' in val.text and ')' in val.text:
                    parts = val.text.replace(')', '').split('(')
                    stars = parts[0]
                    num_reviews = parts[1]
                else:
                    ratings_label = val.get_attribute("aria-label")
                    stars = ratings_label.replace(self.config['stars_text'], '').replace(' ', '')

                    val = self.driver.find_element(By.XPATH, '//*[contains(@aria-label, "' + self.config['reviews_text'] + '")]')
                    ratings_label = val.get_attribute("aria-label")
                    num_reviews = ratings_label.replace(self.config['reviews_text'], '').replace(' ', '')

                place.stars = self.check_rating(stars)
                place.reviews = self.check_rating(num_reviews)
                print(f"[DEBUG] Stars: {place.stars}, Reviews: {place.reviews}")
            except Exception as e:
                print(f"[DEBUG] Could not get stars/reviews: {e}")

            # Image
            try:
                img_src = self.driver.find_element(By.XPATH, '//img[@decoding="async"]').get_attribute("src")
                if not 'gstatic' in img_src or not 'streetviewpixels' in img_src:
                    filename = kw.lower()
                    filename = self.remove_accents(filename)
                    filename = re.sub(r'[^\w\s-]', '', filename)
                    filename = filename.replace(' ', '-')
                    filename = re.sub(r'-+', '-', filename)
                    full_path = f"{self.img_output}{filename}.jpg"
                    urllib.request.urlretrieve(img_src, full_path)
                    print(f"[DEBUG] Image saved: {full_path}")
            except Exception as e:
                print(f"[DEBUG] Unable to obtain the image: {e}")

            # Category
            try:
                place.category = self.find_by_xpath('//button[contains(@jsaction, "pane.") and contains(@jsaction, ".category")]')
            except:
                place.category = ''

            # Address
            try:
                address_label = self.driver.find_element(By.XPATH, '//*[contains(@aria-label, "' + self.config['address_text'] + '")]').get_attribute('aria-label')
                place.address = address_label.replace(self.config['address_text'], "").strip()
            except:
                place.address = ''

            # Website
            try:
                web_label = self.driver.find_element(By.XPATH, '//*[contains(@aria-label, "' + self.config['website_text'] + '")]').get_attribute('aria-label')
                place.web = web_label.replace(self.config['website_text'], "").strip()
            except:
                place.web = ''

            # Phone
            try:
                phone_label = self.driver.find_element(By.XPATH, '//*[contains(@aria-label, "' + self.config['phone_text'] + '")]').get_attribute('aria-label')
                place.phone = phone_label.replace(self.config['phone_text'], "").strip()
            except:
                place.phone = ''

            # Plus Code
            try:
                pluscode_label = self.driver.find_element(By.XPATH, '//*[contains(@aria-label, "' + self.config['pluscode_text'] + '")]').get_attribute('aria-label')
                place.pluscode = pluscode_label.replace(self.config['pluscode_text'], "").strip()
            except:
                place.pluscode = ''

            place.hours = self.get_hours()

            print(f"[DEBUG] Scrape complete for: {place.name}")

            # Scrape reviews
            place.csv_path = self.scrape_reviews(kw, num_reviews=200)

            return place
        except Exception as e:
            print(f"[DEBUG] Error in scrape_place: {e}")
            self.error_count += 1
            return None

    def find_by_xpath(self, xpath):
        try:
            return self.driver.find_element(By.XPATH, xpath).text
        except:
            return ''

    def wait_element(self, xpath, timeout):
        try:
            return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
        except Exception as e:
            print(f"Error waiting for element: {xpath} - {e}")
            return None

    def get_hours(self):
        try:
            hours = self.driver.find_element(By.XPATH, '//*[contains(@aria-label, "' + self.config['hours_text'] + '")]').get_attribute('aria-label')
            hours = hours.replace(self.config['hours_replace'][0], '')
            hours = hours.replace(self.config['hours_replace'][1], '')
            hours = hours.replace(self.config['hours_replace'][2], '\n')
            return hours
        except:
            return ''

    def is_loaded(self, kw):
        # No longer needed — handled directly in scrape_place now
        return True

    def check_rating(self, val):
        if self.config['stars_text'] in val or self.config['reviews_text'] in val:
            return ''
        else:
            return val

    def scrape_reviews(self, kw, num_reviews=200):
        """
        Scrape reviews for the current place and save to CSV.
        Must be called after scrape_place() has already opened a place.
        """
        try:
            reviews_data = []

            # Click on the Reviews tab
            try:
                reviews_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[@role="tab" and contains(@aria-label, "Reviews")]'))
                )
                reviews_button.click()
                print("[DEBUG] Clicked Reviews tab")
                time.sleep(2)

                # Sort by Newest
                try:
                    print("[DEBUG] Attempting to sort by Newest...")
                    sort_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, f'//button[.//span[text()="{self.config["sort_text"]}"]] | //span[contains(@class, "GMtm7c") and text()="{self.config["sort_text"]}"]/ancestor::button'))
                    )
                    sort_button.click()
                    time.sleep(1)

                    newest_option = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, f'//div[@role="menuitemradio" and .//div[text()="{self.config["newest_text"]}"]] | //div[text()="{self.config["newest_text"]}"] | //button[.//div[text()="{self.config["newest_text"]}"]]'))
                    )
                    newest_option.click()
                    print(f"[DEBUG] Sorted by {self.config['newest_text']}")
                    time.sleep(2)
                except Exception as e:
                    print(f"[DEBUG] Could not sort by Newest: {e}")

                # Wait for reviews to load
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.jftiEf, div[data-review-id], div.MyEned'))
                    )
                    print("[DEBUG] Reviews loaded")
                except:
                    print("[DEBUG] Reviews taking long to load, continuing anyway...")

                time.sleep(2)

            except Exception as e:
                print(f"[DEBUG] Could not click Reviews tab: {e}")
                return None

            # Scroll to load more reviews using dynamic container detection
            scrollable_div = None

            # Save page source for debugging
            try:
                debug_html_path = f'{self.img_output}page_source_reviews.html'
                with open(debug_html_path, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print(f"[DEBUG] Saved page source to: {debug_html_path}")
            except Exception as e:
                print(f"[DEBUG] Failed to save page source: {e}")

            try:
                debug_screenshot_path = f'{self.img_output}debug_reviews_tab.png'
                self.driver.save_screenshot(debug_screenshot_path)
                print(f"[DEBUG] Saved screenshot to: {debug_screenshot_path}")
            except Exception as e:
                print(f"[DEBUG] Failed to save screenshot: {e}")

            # Use JavaScript to find the scrollable container dynamically
            try:
                print("[DEBUG] Using JavaScript to find scrollable container...")

                find_scrollable_script = """
                function findScrollableReviewsContainer() {
                    const allDivs = document.querySelectorAll('div');
                    const scrollableDivs = [];

                    for (let div of allDivs) {
                        if (div.scrollHeight > div.clientHeight && div.clientHeight > 100) {
                            const hasReviewContent = div.querySelector('span[role="img"]') !== null ||
                                                    div.textContent.includes('star') ||
                                                    div.querySelector('div.jftiEf') !== null ||
                                                    div.querySelector('div[data-review-id]') !== null;

                            if (hasReviewContent) {
                                scrollableDivs.push({
                                    element: div,
                                    scrollHeight: div.scrollHeight,
                                    clientHeight: div.clientHeight,
                                    className: div.className
                                });
                            }
                        }
                    }

                    scrollableDivs.sort((a, b) => b.scrollHeight - a.scrollHeight);
                    return scrollableDivs.length > 0 ? scrollableDivs[0].element : null;
                }

                return findScrollableReviewsContainer();
                """

                scrollable_div = self.driver.execute_script(find_scrollable_script)

                if scrollable_div:
                    print("[DEBUG] Found scrollable container via JavaScript")

                    for i in range(40):
                        self.driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
                        time.sleep(0.5)
                        if (i + 1) % 5 == 0:
                            print(f"[DEBUG] Scrolled {i+1}/40 times")

                    print("[DEBUG] JavaScript scrolling complete")
                else:
                    print("[DEBUG] No scrollable container found via JavaScript")

            except Exception as e:
                print(f"[DEBUG] JavaScript method failed: {e}")

                # FALLBACK 1: focus + keyboard scrolling
                try:
                    print("[DEBUG] Trying fallback: focus + keyboard scrolling...")

                    try:
                        sort_button = self.driver.find_element(By.XPATH, '//button[contains(@aria-label, "Sort")]')
                        sort_button.click()
                        time.sleep(0.5)
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        time.sleep(0.5)
                    except:
                        pass

                    main_panel = self.driver.find_element(By.CSS_SELECTOR, 'div[role="main"]')
                    main_panel.click()
                    time.sleep(0.5)

                    for i in range(20):
                        main_panel.send_keys(Keys.PAGE_DOWN)
                        time.sleep(0.3)
                        if (i + 1) % 5 == 0:
                            print(f"[DEBUG] Fallback Page Down {i+1}/20")

                    print("[DEBUG] Fallback keyboard scrolling complete")

                except Exception as e2:
                    print(f"[DEBUG] Fallback keyboard method also failed: {e2}")

                    # FALLBACK 2: hardcoded class names as last resort
                    try:
                        print("[DEBUG] Trying last resort: hardcoded selectors...")
                        scrollable_candidates = self.driver.find_elements(By.CSS_SELECTOR, 'div.m6QErb, div.DxyBCb')

                        for candidate in scrollable_candidates:
                            try:
                                for i in range(10):
                                    self.driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', candidate)
                                    time.sleep(0.5)
                                print("[DEBUG] Hardcoded selector scrolling complete")
                                break
                            except:
                                continue
                    except Exception as e3:
                        print(f"[DEBUG] All scrolling methods failed: {e3}")

            # Save screenshot after scrolling
            try:
                self.driver.save_screenshot(f'{self.img_output}debug_after_scrolling.png')
                print("[DEBUG] Saved screenshot after scrolling")
            except:
                pass

            # Try multiple selectors to find reviews
            review_elements = []

            # Method 1: jftiEf class (common review wrapper)
            review_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.jftiEf')
            if len(review_elements) > 0:
                print(f"[DEBUG] Found {len(review_elements)} reviews using jftiEf class")

            # Method 2: data-review-id attribute
            if len(review_elements) == 0:
                review_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-review-id]')
                if len(review_elements) > 0:
                    print(f"[DEBUG] Found {len(review_elements)} reviews using data-review-id")

            # Method 3: MyEned class (another review container)
            if len(review_elements) == 0:
                review_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.MyEned')
                if len(review_elements) > 0:
                    print(f"[DEBUG] Found {len(review_elements)} reviews using MyEned class")

            # Method 4: WNxzHc class
            if len(review_elements) == 0:
                review_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.WNxzHc')
                if len(review_elements) > 0:
                    print(f"[DEBUG] Found {len(review_elements)} reviews using WNxzHc class")

            # Method 5: XPath pattern
            if len(review_elements) == 0:
                review_elements = self.driver.find_elements(By.XPATH, '//div[contains(@class, "fontBodyMedium") and .//span[@role="img"]]')
                if len(review_elements) > 0:
                    print(f"[DEBUG] Found {len(review_elements)} reviews using XPath pattern")

            if len(review_elements) == 0:
                print("[DEBUG] Could not find any reviews with any selector")
                with open(f'{self.img_output}debug_no_reviews.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print("[DEBUG] Saved debug_no_reviews.html for inspection")
                return None

            seen_reviews = set()  # Track unique reviews by reviewer name + date

            for idx, review_elem in enumerate(review_elements[:num_reviews * 2]):
                if len(reviews_data) >= num_reviews:
                    break

                try:
                    # Expand truncated reviews
                    try:
                        more_button = review_elem.find_element(By.CSS_SELECTOR, 'button[aria-label*="See more"]')
                        more_button.click()
                        time.sleep(0.3)
                    except:
                        pass

                    # Extract review data
                    reviewer_name = ""
                    rating = ""
                    review_text = ""
                    review_date = ""

                    # Reviewer name
                    try:
                        reviewer_name = review_elem.find_element(By.CSS_SELECTOR, 'div.d4r55').text
                    except:
                        pass

                    # Rating (stars)
                    try:
                        rating_elem = review_elem.find_element(By.CSS_SELECTOR, 'span[role="img"]')
                        rating = rating_elem.get_attribute('aria-label').split()[0]
                    except:
                        pass

                    # Review text
                    try:
                        review_text = review_elem.find_element(By.CSS_SELECTOR, 'span.wiI7pd').text
                    except:
                        pass

                    # Date
                    try:
                        review_date = review_elem.find_element(By.CSS_SELECTOR, 'span.rsqaWe').text
                    except:
                        pass

                    # Skip duplicates
                    review_key = f"{reviewer_name}_{review_date}"
                    if review_key in seen_reviews:
                        continue

                    seen_reviews.add(review_key)

                    reviews_data.append({
                        'reviewer_name': reviewer_name,
                        'rating': rating,
                        'date': review_date,
                        'review_text': review_text
                    })

                    print(f"[DEBUG] Scraped review {len(reviews_data)}: {reviewer_name}")

                except Exception as e:
                    print(f"[DEBUG] Error scraping review {idx}: {e}")
                    continue

            # Save to CSV
            if reviews_data:
                filename = kw.lower()
                filename = self.remove_accents(filename)
                filename = re.sub(r'[^\w\s-]', '', filename)
                filename = filename.replace(' ', '-')
                filename = re.sub(r'-+', '-', filename)

                csv_path = f"{self.img_output}{filename}_reviews.csv"

                with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['reviewer_name', 'rating', 'date', 'review_text']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(reviews_data)

                print(f"[DEBUG] Saved {len(reviews_data)} reviews to {csv_path}")
                return csv_path
            else:
                print("[DEBUG] No reviews found to save")
                return None

        except Exception as e:
            print(f"[DEBUG] Error in scrape_reviews: {e}")
            return None

    def quit_driver(self):
        self.driver.quit()