const config = require('./config');

let currentWord = '';
let currentLanguage = '';

/**
 * A mapping of card types to their corresponding icon and title for tooltips.
 */
const cardIconMapping = {
    'Direct Translation': { icon: '⇄', title: 'Direct Translation' },
    'Related Vocabulary': { icon: '🏷️', title: 'Related Vocabulary' },
    'Practical Usage': { icon: '💬', title: 'Practical Usage' },
    'Advanced Content': { icon: '📖', title: 'Advanced Content' }
};

/**
 * Reusable function to fetch lesson data from the backend.
 * @param {string} word The word to get a lesson for.
 * @param {string} language The target language.
 * @returns {Promise<object>} The lesson data as a JSON object.
 */
async function fetchLessonData(word, language) {
    try {
        const response = await fetch(config.urlContextEngine, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word, foreignLanguage: language })
        });

        const data = await response.json();

        if (response.ok) {
            return data;
        } else {
            throw new Error(data.error || 'An unknown error occurred.');
        }
    } catch (error) {
        console.error('Failed to fetch lesson data:', error);
        alert(`An error occurred: ${error.message}`);
        throw error; // Re-throw to be caught by the caller
    }
}

/**
 * Parses a string with Furigana and converts it to HTML <ruby> elements.
 * e.g., "日本語(にほんご)" -> "<ruby>日本語<rt>にほんご</rt></ruby>"
 * @param {string} text - The text containing Furigana in parentheses.
 * @returns {string} The HTML string with <ruby> tags.
 */
function parseFurigana(text) {
    if (!text) return '';
    // Regex to find Kanji followed by Furigana in parentheses
    const furiganaRegex = /([\u4e00-\u9faf]+)\(([\u3040-\u309f]+)\)/g;
    return text.replace(furiganaRegex, '<ruby>$1<rt>$2</rt></ruby>');
}

/**
 * Creates a special HTML block for structured Japanese content.
 * @param {object} data - The Japanese content object {lm, lrm, lt}.
 * @returns {HTMLDivElement} The created DOM element for the block.
 */
function createJapaneseBlock(data) {
    const block = document.createElement('div');
    block.className = 'japanese-block';

    // The main line now uses <ruby> tags for Furigana, parsed from the 'lm' field
    const main = document.createElement('p');
    main.className = 'line-main';
    main.innerHTML = parseFurigana(data.lm); // Use innerHTML to render the ruby tags
    block.appendChild(main);

    // Romaji and Translation remain the same
    const romaji = document.createElement('p');
    romaji.className = 'line-romaji';
    romaji.textContent = data.lrm;
    block.appendChild(romaji);

    const translation = document.createElement('p');
    translation.className = 'line-translation';
    translation.textContent = data.lt;
    block.appendChild(translation);

    return block;
}

/**
 * Appends the specific content for a card type to the card's body.
 * @param {HTMLElement} body - The flashcard body element.
 * @param {any} content - The content data for the card.
 * @param {string} type - The type of the card (e.g., 'Related Vocabulary').
 */
function appendCardContent(body, content, type) {
    if (!content) return;

    switch (type) {
        case 'Direct Translation':
            if (typeof content === 'string') {
                const p = document.createElement('p');
                p.textContent = content;
                body.appendChild(p);
            } else if (typeof content === 'object') {
                body.appendChild(createJapaneseBlock(content));
            }
            break;

        case 'Related Vocabulary':
        case 'Practical Usage':
            if (Array.isArray(content)) {
                content.forEach(item => {
                    const itemWrapper = document.createElement('div');
                    itemWrapper.className = 'list-item';

                    const mainContent = item.vocabulary || item.usage;
                    if (typeof mainContent === 'string') {
                        const p = document.createElement('p');
                        p.textContent = `${mainContent} - ${item.translation}`;
                        itemWrapper.appendChild(p);
                    } else if (typeof mainContent === 'object' && mainContent !== null) {
                        itemWrapper.appendChild(createJapaneseBlock(mainContent));
                        const explanation = document.createElement('p');
                        explanation.className = 'item-explanation';
                        explanation.textContent = item.translation;
                        itemWrapper.appendChild(explanation);
                    }
                    body.appendChild(itemWrapper);
                });
            }
            break;

        case 'Advanced Content':
            if (typeof content === 'object' && content !== null) {
                const mainContent = content.content;
                if (typeof mainContent === 'string') {
                    const p = document.createElement('p');
                    p.textContent = mainContent;
                    body.appendChild(p);
                } else if (typeof mainContent === 'object' && mainContent !== null) {
                    body.appendChild(createJapaneseBlock(mainContent));
                }
                const explanation = document.createElement('p');
                explanation.className = 'item-explanation'; // Ensuring "Note" style is applied
                explanation.textContent = content.explanation;
                body.appendChild(explanation);
            }
            break;
    }
}

/**
 * Creates a single flashcard element with an icon header and formatted content.
 * @param {object} cardInfo - An object containing card { type, content, isExtended }.
 * @returns {HTMLDivElement} The created flashcard element.
 */
function createFlashcard(cardInfo) {
    const { type, content, isExtended } = cardInfo;
    const flashcardDiv = document.createElement('div');
    flashcardDiv.className = 'flashcard';

    // 1. Create Header with Icon
    const header = document.createElement('div');
    header.className = 'flashcard-header';

    const iconContainer = document.createElement('div');
    iconContainer.className = 'card-icon-container';

    const iconData = cardIconMapping[type];
    if (iconData) {
        iconContainer.textContent = iconData.icon;
        // Add tooltip for accessibility
        const tooltipTitle = isExtended ? `${iconData.title} (Extended)` : iconData.title;
        iconContainer.setAttribute('title', tooltipTitle);
    }

    header.appendChild(iconContainer);
    flashcardDiv.appendChild(header);

    // 2. Create Content Body
    const body = document.createElement('div');
    body.className = 'flashcard-body';
    appendCardContent(body, content, type);
    flashcardDiv.appendChild(body);

    return flashcardDiv;
}

/**
 * Loads flashcards based on the lesson data.
 * For initial load, clears existing flashcards. For extensions, appends to existing ones.
 * Sets up an IntersectionObserver to animate cards as they scroll into view.
 * @param {object} lesson - The lesson data from the API.
 * @param {boolean} isInitialLoad - Whether this is the first load or an extension.
 */
function loadFlashcards(lesson, isInitialLoad) {
    const flashcardContainer = document.getElementById('flashcard-container');

    // For initial load, clear previous content
    if (isInitialLoad) {
        flashcardContainer.innerHTML = '';
    }

    // Define the order and content of the cards
    const cardsData = isInitialLoad ?
        [
            { type: 'Direct Translation', content: lesson.directTranslation },
            { type: 'Related Vocabulary', content: lesson.relatedVocabulary },
            { type: 'Practical Usage', content: lesson.practicalUsage },
            { type: 'Advanced Content', content: lesson.advancedContent }
        ]
        : [
            { type: 'Related Vocabulary', content: lesson.relatedVocabulary, isExtended: true },
            { type: 'Practical Usage', content: lesson.practicalUsage, isExtended: true },
            { type: 'Advanced Content', content: lesson.advancedContent, isExtended: true }
        ];

    // Create and append all flashcard elements to the DOM
    const cardElements = cardsData
        .filter(cardInfo => cardInfo.content)
        .map(cardInfo => createFlashcard(cardInfo));

    cardElements.forEach(cardEl => flashcardContainer.appendChild(cardEl));

    // Show the load more button after initial load
    if (isInitialLoad && cardElements.length > 0) {
        const loadMoreContainer = document.getElementById('load-more-container');
        loadMoreContainer.remove();
        flashcardContainer.appendChild(loadMoreContainer);
        loadMoreContainer.style.display = 'block';
    }

    // Set up the scroll-triggered animation for the newly created cards
    setupScrollAnimation();
}

/**
 * Initializes an IntersectionObserver to add a 'visible' class to flashcards
 * when they enter the viewport, triggering a one-time animation.
 * This function handles both initial cards and newly added cards.
 */
function setupScrollAnimation() {
    const flashcards = document.querySelectorAll('.flashcard');

    // The first card is visible by default, so we don't need to observe it.
    // This also prevents a "flash" if the observer fires slightly late.
    if (flashcards.length > 0) {
        // Only make the first card visible if it's not already
        if (!flashcards[0].classList.contains('visible')) {
            flashcards[0].classList.add('visible');
        }
    }

    const observerOptions = {
        root: null, // Use the viewport as the root
        rootMargin: '0px',
        // Trigger the animation when a card is 50% visible.
        threshold: 0.5
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            // If the card is intersecting the viewport, make it visible.
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                // Once a card is visible, we don't need to observe it anymore.
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Start observing each flashcard, skipping the first one.
    // Only observe cards that are not already visible
    flashcards.forEach((card, index) => {
        if (index > 0 && !card.classList.contains('visible')) {
            observer.observe(card);
        }
    });
}

// --- Event Listeners ---

document.getElementById('language-form').addEventListener('submit', async (event) => {
    event.preventDefault();

    currentWord = document.getElementById('word-input').value;
    currentLanguage = document.getElementById('foreign-language-select').value;

    if (!currentWord || !currentLanguage) {
        alert('Please enter a word and select a language.');
        return;
    }

    const submitButton = event.target.querySelector('button');
    submitButton.disabled = true;
    submitButton.textContent = 'Generating...';

    try {
        const data = await fetchLessonData(currentWord, currentLanguage);
        loadFlashcards(data, true); // true for initial load
    } catch (error) {
        // Error is already alerted in fetchLessonData
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = 'Generate';
    }
});

document.getElementById('load-more-btn').addEventListener('click', async () => {
    if (!currentWord || !currentLanguage) {
        return;
    }

    const loadMoreBtn = document.getElementById('load-more-btn');
    loadMoreBtn.disabled = true;
    loadMoreBtn.textContent = 'Loading...';

    try {
        const data = await fetchLessonData(currentWord, currentLanguage);
        loadFlashcards(data, false); // false for extension
    } catch (error) {
        // Error is already alerted in fetchLessonData
    } finally {
        loadMoreBtn.disabled = false;
        loadMoreBtn.textContent = 'Load More';
    }
});
