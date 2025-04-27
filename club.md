Below is a plan for adding “Clubs” as a parallel, toggle-able entity alongside Courses. We will reuse as much of the existing code, views, and templates as possible, adding only minimal conditionals and a tiny new bit of model definition.

---

## 1. Models

### 1.1. New `ClubCategory` model

tcf_website/models/models.py  
(Add immediately after the existing Subdepartment or wherever your models cluster.)

```python
class ClubCategory(models.Model):
    # Human name
    name        = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    # slug for routing in the existing course URL
    slug        = models.SlugField(max_length=255, unique=True)

    def __str__(self):
        return self.name
```

- No relationship to Department/Subdepartment.
- `slug` gives us a place to hang on to “mnemonic” in the old course URL.

### 1.2. New `Club` model

tcf_website/models/models.py  

```python
class Club(models.Model):
    name          = models.CharField(max_length=255)
    description   = models.TextField(blank=True)
    category      = models.ForeignKey(ClubCategory, on_delete=models.CASCADE)
    combined_name = models.CharField(max_length=255, blank=True, editable=False)

    def save(self, *args, **kwargs):
        # maintain combined_name for trigram search
        self.combined_name = self.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
```

- After this, add the same trigram GinIndex you have on Course.combined_mnemonic_number, but pointing at `Club.combined_name`.  
- This lets `TrigramSimilarity` work identically.

### 1.3. Extend the existing `Review` model

tcf_website/models/models.py  

Find your `class Review(models.Model):` and add:

```python
    # Existing fields: course = FK(Course)
    club = models.ForeignKey(Club, on_delete=models.CASCADE,
                             null=True, blank=True)
```

Then adjust any unique‐together or constraints so that a user may have one review per (user, course) OR (user, club). Everything else—votes, pagination, sorting—stays untouched.

---

## 2. Pull “mode=clubs” through your views

We will reuse every URL you already have.  
- The existing course‐detail URL is:  
  `/course/<mnemonic>/<course_number>/`  
- In club‐mode we will treat `<mnemonic>` as `ClubCategory.slug` and `<course_number>` as `Club.id`.

### 2.1. Base utility

In a shared module (e.g. at top of each view file) add:

```python
def parse_mode(request):
    mode = request.GET.get("mode", "courses")
    return mode, (mode == "clubs")
```

### 2.2. Search view

tcf_website/views/search.py  

1. At the top of `search(request)`:

   ```python
   mode, is_club = parse_mode(request)
   ```

2. Build two parallel fetch pipelines:

   - **fetch_courses(query, filters)** (already exists)  
   - **fetch_clubs(query)** ← a new helper that does:

     ```python
     from django.contrib.postgres.search import TrigramSimilarity
     from ..models import Club

     def fetch_clubs(query):
         threshold = 0.15
         qs = (Club.objects
               .annotate(sim=TrigramSimilarity("combined_name", query))
               .annotate(max_similarity=F("sim"))
               .filter(max_similarity__gte=threshold)
               .order_by("-max_similarity")[:15])
         return [
             {"id": c.id, "name": c.name, "description": c.description,
              "max_similarity": c.max_similarity,
              "category_slug": c.category.slug,
              "category_name": c.category.name}
             for c in qs
         ]
     ```

3. In `search()`:

   ```python
   if is_club:
       clubs = fetch_clubs(query)
       grouped = group_by_club_category(clubs)
       total = len(clubs)
   else:
       courses = fetch_courses(query, filters)
       grouped = group_by_dept(courses)
       total = len(courses)
   ```

4. New grouping helper:

   ```python
   def group_by_club_category(clubs):
       grouped = {}
       for cb in clubs:
           slug = cb["category_slug"]
           if slug not in grouped:
               grouped[slug] = {
                   "category_name": cb["category_name"],
                   "category_slug": slug,
                   "clubs": []
               }
           grouped[slug]["clubs"].append(cb)
       return grouped
   ```

5. Context:

   ```python
   ctx = {
     "mode": mode,
     "is_club": is_club,
     "query": truncated_query,
     ...
     "total": total,
     "grouped": grouped,
     # keep your old keys for courses/instructors if !is_club
   }
   ```

### 2.3. Course/Club detail view

tcf_website/views/browse.py → `course_view`

1. At top:

   ```python
   mode, is_club = parse_mode(request)
   ```

2. Branch:

   ```python
   if is_club:
       # 'mnemonic' is actually category_slug, 'course_number' is club.id
       club = get_object_or_404(Club, id=course_number,
                                category__slug=mnemonic.upper())
       # Pull reviews exactly as you do for courses, but filter on club=club
       paginated_reviews = Review.get_paginated_reviews(
           course_id=None,
           instructor_id=None,
           user=request.user,
           page_number=request.GET.get("page", 1),
           mode="clubs",  # pass through so templates know
           club=club.id
       )
       return render(request, "course/course.html", {
           "is_club": True,
           "club": club,
           "paginated_reviews": paginated_reviews,
           "sort_method": request.GET.get("method", ""),
           # plus any other bits you need (e.g. data for JS)
       })
   else:
       # <<< existing course logic >>>
       return render(request, "course/course.html", {
         "is_club": False,
         "course": course,
         "instructors": instructors,
         ...
       })
   ```

   - We reuse **exactly** the same template name (`course/course.html`) but tell it via `is_club` to switch into club‐rendering mode.

---

## 3. Reviews and Review-form views

Wherever you currently do:

```python
# for new_review, edit_review, check_duplicate, etc.
course_id = request.POST.get("course")
duplicate = Review.objects.filter(user=request.user, course=course_id).exists()
```

you’ll now:

1. parse `mode, is_club = parse_mode(request)`  
2. read either `club_id = request.POST.get("club")` *or* the old `course` field  
3. branch your Filter/Exists/Save logic on `is_club` and set the FK on the new Review accordingly.  
4. carry `mode=clubs` in your redirect so that after POST you come back to the club detail page.

The HTML form (`review_form_content.html`) itself can gain a tiny `if is_club` wrapper around the course‐picker widget, replacing “Subject/Course/Instructor” selects with “Category/Club” selects:

```django
{% if not is_club %}
  <!-- existing subject/course/instructor selects -->
{% else %}
  <div class="form-row">
    <div class="form-group col-sm-6">
      <label for="category">Category</label>
      <select id="category" name="category" class="form-control" required>
        {% for cat in club_categories %}
          <option value="{{ cat.id }}" {% if cat.id == form.instance.club.category.id %}selected{% endif %}>
            {{ cat.name }}
          </option>
        {% endfor %}
      </select>
    </div>
    <div class="form-group col-sm-6">
      <label for="club">Club</label>
      <select id="club" name="club" class="form-control" required>
        <option value="{{ form.instance.club.id }}">{{ form.instance.club.name }}</option>
      </select>
    </div>
  </div>
{% endif %}
```

– You won’t need instructor or semester selects for clubs, so you can omit or hide those.

---

## 4. Templates

We’ll continue to reuse **exactly** the same file names.  
Everywhere you currently reference `course`, `instructor`, or “Departments,” wrap them in:

```django
{% if not is_club %}
  <!-- original markup -->
{% else %}
  <!-- minimal club‐specific markup, or include from club/ -->
{% endif %}
```

### 4.1. Create `templates/club/`

#### 4.1.1. `templates/club/club.html`

Copy `course/course.html`, then:

- Change all `course.` → `club.`  
- Remove the instructor‐loop entirely  
- Add the “Reviews” and the Q&A tabs from `course/course_professor.html`

### 4.2. Integrate into search & nav

#### In your search bar partial

Add:

```html
<select name="mode" class="form-control">
  <option value="courses" {% if not is_club %}selected{% endif %}>Courses</option>
  <option value="clubs"    {% if  is_club %}selected{% endif %}>Clubs</option>
</select>
```

#### In `templates/search/search.html`

- Replace the three‐tab header with either your old “Courses/Instructors/Departments” OR a single “Clubs” panel:  

```django
{% if not is_club %}
  <!-- existing 3‐tab markup -->
{% else %}
  <!-- show just one tab: Clubs -->
  <div id="clubs" class="collapse show">
    {% include "club/club_search_results.html" %}
  </div>
{% endif %}
```

- Write `club_search_results.html` by copying the “Courses” block and swapping `c.mnemonic c.number c.title` → `club.name` + optional description collapse.

### 4.3. All review templates

In every review include (`review.html`, `reviews.html`, modals, user_reviews, etc.):

- If you render a link back to the detail page, replace the `url 'course' mnemonic=c.mnemonic course_number=c.number` with:

  ```django
  {% if not is_club %}
    {% url 'course' mnemonic=review.course.subdepartment.mnemonic course_number=review.course.number %}
  {% else %}
    {% url 'course' mnemonic=review.club.category.slug course_number=review.club.id %}?mode=clubs
  {% endif %}
  ```

- Everywhere you refer to `review.course` vs `review.instructor`, branch off `if review.club` or `is_club`.

---

## 5. No URL changes

We’re still hitting:

```
/search/?q=Foo&mode=clubs
/course/<slug>/<id>/?mode=clubs
/reviews/new/?mode=clubs
```

The routers in `urls.py` stay untouched.

---

## 6. Final sanity check

1. **Models**  
   – `ClubCategory(slug)`  
   – `Club(category)`  
   – `Review.club`  

2. **Views**  
   – `search` → `fetch_clubs` + `group_by_club_category`  
   – `course_view` → branch on `is_club`  
   – review‐form + duplicate/zero‐hours checks → branch on `is_club`  

3. **Templates**  
   – Single search bar toggle  
   – Single URL pattern reused with `?mode=clubs`  
   – `{% if is_club %}{% include "club/…"%}` wrappers in all course pages  
   – Two new partials: `templates/club/club.html` + `…/club_detail.html`  
   – Adjust all review‐link URL generations to carry `club` vs `course`.  

With this in place, **every** piece of review logic, every JS snippet, every widget, every form, and every template partial is *exactly* the same as before—only switched on a single `mode=clubs` flag.
