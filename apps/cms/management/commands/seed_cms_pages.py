"""Seed the public CMS pages (about, terms, privacy, contact, faq).

Usage: python manage.py seed_cms_pages

The content is a starting point — replace the bracketed placeholders and have
a lawyer review the terms/privacy before launch.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.cms.models import CMSPage

PAGES = {
    "about": (
        "About us",
        """
        <p>[Your company name] operates this rewards platform. Users earn rewards
        for playing games, completing surveys and finishing verified offers, and
        withdraw through supported payment methods.</p>
        <p>Registered address: [address]. Contact: [support email].</p>
        <p>We work with third-party advertising and survey providers. Rewards are
        only credited after a provider confirms a valid completion.</p>
        """,
    ),
    "terms": (
        "Terms of Service",
        """
        <p>By creating an account you agree to these terms.</p>
        <ul>
          <li>You must be [18+] and provide accurate information.</li>
          <li>One account per person. Multiple accounts, emulators, VPN/proxy
              use to bypass offer rules, or automated activity may result in
              suspension and forfeiture of rewards.</li>
          <li>Offers and surveys are provided by third parties. Their campaign
              rules (country, device, completion limits) are shown before you
              start and must be respected.</li>
          <li>Rewards may be <strong>reversed</strong> if a provider rejects a
              conversion. Reversals appear in your transaction history.</li>
          <li>Provider approval and processing times vary; pending rewards are
              not withdrawable until approved.</li>
          <li>Withdrawals may require identity verification above [threshold]
              and may be delayed for review where fraud is suspected.</li>
          <li>We may suspend accounts that breach these terms or applicable law.</li>
        </ul>
        <p>This is a starting template — have it reviewed by a qualified lawyer
        before launch.</p>
        """,
    ),
    "privacy": (
        "Privacy Policy",
        """
        <p>We collect the minimum data needed to operate the platform:</p>
        <ul>
          <li>Account data: email, optional profile details.</li>
          <li>Activity data: game sessions, offer and survey completions,
              rewards and wallet transactions.</li>
          <li>Risk data: IP address, device signals and session information
              used for fraud prevention.</li>
          <li>Payment data: withdrawal method details and payment references.</li>
        </ul>
        <p>We share the data required with third-party providers (advertising,
        survey and payment partners) to verify completions and process payments.
        Cookies and similar technologies are used for sessions, security and
        analytics.</p>
        <p>You can request access to or deletion of your data by contacting
        [support email]; financial records may be retained where the law
        requires it.</p>
        <p>This is a starting template — have it reviewed by a qualified lawyer
        before launch.</p>
        """,
    ),
    "contact": (
        "Contact",
        """
        <p>Support: [support email]</p>
        <p>Business address: [address]</p>
        <p>Support hours: [hours]. For payment or offer issues, include your
        account email and the transaction ID from your history page.</p>
        """,
    ),
    "faq": (
        "Frequently asked questions",
        """
        <ul>
          <li><strong>When do I get my reward?</strong> Rewards are pending
              first, then become available after the provider confirms them.</li>
          <li><strong>Why was my reward reversed?</strong> The provider rejected
              the completion (for example the offer was not completed per their
              rules). The reversal is shown in your history.</li>
          <li><strong>Why can't I see some offers?</strong> Offers are shown
              only when the campaign allows your country, device and traffic
              type, and when you have completions left.</li>
          <li><strong>How long do withdrawals take?</strong> After approval,
              payouts are processed per the method's schedule; some methods are
              manual and may take longer.</li>
        </ul>
        """,
    ),
}


class Command(BaseCommand):
    help = "Create/update the public CMS pages."

    def handle(self, *args, **options):
        now = timezone.now()
        for slug, (title, content) in PAGES.items():
            page, created = CMSPage.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "content": content.strip(),
                    "status": CMSPage.Status.PUBLISHED,
                    "published_at": now,
                },
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"{page.slug}: {'created' if created else 'updated'} (published)"
                )
            )
        self.stdout.write("Replace the [bracketed] placeholders before launch.")
