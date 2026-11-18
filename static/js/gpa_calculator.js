(() => {
  const calculator = document.querySelector('#gpa-calculator');
  const curriculum = JSON.parse(document.querySelector('#gpa-curriculum').textContent);
  const sgpaForm = document.querySelector('#sgpa-form');
  const semesterSelect = document.querySelector('#gpa-semester');
  const subjects = document.querySelector('#sgpa-subjects');
  const internshipHelp = document.querySelector('#internship-help');
  const sgpaRows = document.querySelector('#sgpa-rows');
  const sgpaTemplate = document.querySelector('#sgpa-row');
  const semesterRows = new Map();

  const cgpaForm = document.querySelector('#cgpa-form');
  const cgpaRows = document.querySelector('#cgpa-rows');
  const cgpaTemplate = document.querySelector('#cgpa-row');
  const addButton = document.querySelector('#cgpa-add');
  const semesterNumbers = Object.keys(curriculum).map(Number);
  const cgpaEntries = new Map();

  function createSubjectRow([name, credits]) {
    const row = sgpaTemplate.content.firstElementChild.cloneNode(true);
    row.querySelector('.gpa-subject-name').textContent = name;
    row.querySelector('select').setAttribute('aria-label', `Grade for ${name}`);
    if (credits === null) {
      row.querySelector('.gpa-credit-label').hidden = false;
      row.querySelector('input').disabled = false;
    } else {
      const creditText = row.querySelector('.gpa-credit-text');
      creditText.dataset.credits = credits;
      creditText.textContent = `${credits} ${credits === 1 ? 'credit' : 'credits'}`;
    }
    return row;
  }

  function showResult(mode, entries) {
    let totalCredits = 0;
    let weightedPoints = 0;
    for (const [points, credits] of entries) {
      totalCredits += credits;
      weightedPoints += points * credits;
    }
    const average = weightedPoints / totalCredits;
    const rounded = Math.round((average + Number.EPSILON * average) * 100) / 100;
    document.querySelector(`#${mode}-result`).hidden = false;
    document.querySelector(`#${mode}-value`).value = rounded.toFixed(2);
    document.querySelector(`#${mode}-credits`).textContent =
      `${totalCredits} ${totalCredits === 1 ? 'credit' : 'credits'} included`;
  }

  function updateSgpa() {
    const rows = Array.from(sgpaRows.children);
    if (!rows.length || !sgpaForm.matches(':valid')) {
      document.querySelector('#sgpa-result').hidden = true;
      return;
    }
    showResult('sgpa', rows.map(row => {
      const fixedCredits = row.querySelector('.gpa-credit-text').dataset.credits;
      const credits = fixedCredits ? Number(fixedCredits) : row.querySelector('input').valueAsNumber;
      return [Number(row.querySelector('select').value), credits];
    }));
  }

  semesterSelect.addEventListener('change', () => {
    const semester = semesterSelect.value;
    const courses = curriculum[semester];
    if (courses && !semesterRows.has(semester)) {
      semesterRows.set(semester, courses.map(createSubjectRow));
    }
    sgpaRows.replaceChildren(...(semesterRows.get(semester) ?? []));
    subjects.hidden = !courses;
    internshipHelp.hidden = !courses?.some(([, credits]) => credits === null);
    updateSgpa();
  });
  sgpaRows.addEventListener('input', updateSgpa);
  sgpaForm.addEventListener('submit', event => {
    event.preventDefault();
    updateSgpa();
    document.querySelector('#sgpa-result').scrollIntoView({block: 'nearest'});
  });

  function clearCgpa() {
    document.querySelector('#cgpa-result').hidden = true;
  }

  function updateCgpaControls() {
    addButton.disabled = cgpaEntries.size === semesterNumbers.length;
    for (const row of cgpaEntries.values()) {
      row.querySelector('.gpa-remove').hidden = cgpaEntries.size === 1;
    }
    clearCgpa();
  }

  function addSemester(focus = false) {
    const semester = semesterNumbers.find(number => !cgpaEntries.has(number));
    if (semester === undefined) return;

    const row = cgpaTemplate.content.firstElementChild.cloneNode(true);
    row.querySelector('legend').textContent = `Semester ${semester}`;
    const removeButton = row.querySelector('.gpa-remove');
    removeButton.setAttribute('aria-label', `Remove Semester ${semester}`);
    removeButton.addEventListener('click', () => {
      row.remove();
      cgpaEntries.delete(semester);
      updateCgpaControls();
      addButton.focus();
    });

    const nextSemester = semesterNumbers.find(number => number > semester && cgpaEntries.has(number));
    cgpaRows.insertBefore(row, cgpaEntries.get(nextSemester) ?? null);
    cgpaEntries.set(semester, row);
    updateCgpaControls();
    if (focus) row.querySelector('input').focus();
  }

  addButton.addEventListener('click', () => addSemester(true));
  cgpaForm.addEventListener('input', clearCgpa);
  cgpaForm.addEventListener('submit', event => {
    event.preventDefault();
    const entries = Array.from(cgpaEntries.values(), row => {
      const [sgpa, credits] = row.querySelectorAll('input');
      return [sgpa.valueAsNumber, credits.valueAsNumber];
    });
    showResult('cgpa', entries);
    document.querySelector('#cgpa-result').scrollIntoView({block: 'nearest'});
  });

  calculator.querySelectorAll('[name="gpa-mode"]').forEach(option => {
    option.addEventListener('change', () => {
      sgpaForm.hidden = option.value !== 'sgpa';
      cgpaForm.hidden = option.value !== 'cgpa';
    });
  });

  addSemester();
  calculator.hidden = false;
})();
