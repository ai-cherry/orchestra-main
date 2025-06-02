#!/usr/bin/env node

/**
 * Security audit script for admin-ui
 * Runs comprehensive security checks on pnpm dependencies
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const AUDIT_LEVELS = ['low', 'moderate', 'high', 'critical'];
const ACCEPTABLE_LEVEL = process.env.AUDIT_LEVEL || 'high';

// Color codes for terminal output
const colors = {
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    reset: '\x1b[0m'
};

function log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
}

function runCommand(command, options = {}) {
    try {
        return execSync(command, { encoding: 'utf8', ...options });
    } catch (error) {
        if (options.allowFailure) {
            return error.stdout || error.stderr || '';
        }
        throw error;
    }
}

async function checkPnpmLockExists() {
    const lockPath = path.join(process.cwd(), 'pnpm-lock.yaml');
    if (!fs.existsSync(lockPath)) {
        log('❌ pnpm-lock.yaml not found!', 'red');
        log('Run "pnpm install" to generate lock file', 'yellow');
        return false;
    }
    log('✅ pnpm-lock.yaml found', 'green');
    return true;
}

async function runPnpmAudit() {
    log('\n🔍 Running pnpm audit...', 'blue');

    try {
        const auditResult = runCommand('pnpm audit --json', { allowFailure: true });
        const audit = JSON.parse(auditResult);

        const summary = audit.metadata?.vulnerabilities || {};
        const total = Object.values(summary).reduce((acc, val) => acc + val, 0);

        if (total === 0) {
            log('✅ No vulnerabilities found!', 'green');
            return { success: true, vulnerabilities: 0 };
        }

        log(`\n⚠️  Found ${total} vulnerabilities:`, 'yellow');
        Object.entries(summary).forEach(([level, count]) => {
            if (count > 0) {
                const color = level === 'critical' || level === 'high' ? 'red' : 'yellow';
                log(`  ${level}: ${count}`, color);
            }
        });

        // Check if we exceed acceptable level
        const levelIndex = AUDIT_LEVELS.indexOf(ACCEPTABLE_LEVEL);
        const criticalCount = AUDIT_LEVELS.slice(levelIndex)
            .reduce((acc, level) => acc + (summary[level] || 0), 0);

        if (criticalCount > 0) {
            log(`\n❌ Found ${criticalCount} vulnerabilities at or above ${ACCEPTABLE_LEVEL} level`, 'red');
            return { success: false, vulnerabilities: criticalCount };
        }

        return { success: true, vulnerabilities: total };
    } catch (error) {
        log('❌ Failed to run pnpm audit', 'red');
        console.error(error.message);
        return { success: false, vulnerabilities: -1 };
    }
}

async function checkOutdatedPackages() {
    log('\n📦 Checking for outdated packages...', 'blue');

    try {
        const outdated = runCommand('pnpm outdated --format json', { allowFailure: true });
        const packages = JSON.parse(outdated || '[]');

        if (packages.length === 0) {
            log('✅ All packages are up to date!', 'green');
            return;
        }

        log(`\n📋 Found ${packages.length} outdated packages:`, 'yellow');

        // Group by update type
        const major = packages.filter(p => p.current && p.latest &&
            p.current.split('.')[0] !== p.latest.split('.')[0]);
        const minor = packages.filter(p => p.current && p.latest &&
            p.current.split('.')[0] === p.latest.split('.')[0] &&
            p.current.split('.')[1] !== p.latest.split('.')[1]);
        const patch = packages.filter(p => !major.includes(p) && !minor.includes(p));

        if (major.length > 0) {
            log('\n  Major updates available:', 'red');
            major.forEach(p => {
                log(`    ${p.name}: ${p.current} → ${p.latest}`, 'red');
            });
        }

        if (minor.length > 0) {
            log('\n  Minor updates available:', 'yellow');
            minor.forEach(p => {
                log(`    ${p.name}: ${p.current} → ${p.latest}`, 'yellow');
            });
        }

        if (patch.length > 0) {
            log('\n  Patch updates available:', 'green');
            patch.slice(0, 5).forEach(p => {
                log(`    ${p.name}: ${p.current} → ${p.latest}`, 'green');
            });
            if (patch.length > 5) {
                log(`    ... and ${patch.length - 5} more`, 'green');
            }
        }
    } catch (error) {
        log('⚠️  Could not check for outdated packages', 'yellow');
    }
}

async function checkUnusedDependencies() {
    log('\n🧹 Checking for unused dependencies...', 'blue');

    // Simple check - look for imports in src files
    const srcPath = path.join(process.cwd(), 'src');
    if (!fs.existsSync(srcPath)) {
        log('⚠️  No src directory found, skipping unused dependency check', 'yellow');
        return;
    }

    try {
        const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
        const dependencies = Object.keys(packageJson.dependencies || {});
        const devDependencies = Object.keys(packageJson.devDependencies || {});

        // This is a simple heuristic - in production, use a tool like depcheck
        log('ℹ️  Note: For comprehensive unused dependency detection, consider using depcheck', 'blue');

        const totalDeps = dependencies.length + devDependencies.length;
        log(`  Total dependencies: ${totalDeps} (${dependencies.length} prod, ${devDependencies.length} dev)`, 'blue');
    } catch (error) {
        log('⚠️  Could not analyze dependencies', 'yellow');
    }
}

async function generateSecurityReport() {
    const reportPath = path.join(process.cwd(), 'security-report.json');
    const report = {
        timestamp: new Date().toISOString(),
        auditLevel: ACCEPTABLE_LEVEL,
        checks: {}
    };

    log('\n📊 Generating security report...', 'blue');

    try {
        // Run all checks and collect results
        const auditResult = await runPnpmAudit();
        report.checks.audit = auditResult;

        // Save report
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        log(`✅ Security report saved to ${reportPath}`, 'green');

        return report;
    } catch (error) {
        log('❌ Failed to generate security report', 'red');
        console.error(error);
        return null;
    }
}

// Main execution
async function main() {
    log('🔒 Orchestra AI Admin UI Security Audit', 'blue');
    log('=====================================\n', 'blue');

    // Check prerequisites
    const hasLockFile = await checkPnpmLockExists();
    if (!hasLockFile) {
        process.exit(1);
    }

    // Run security checks
    const auditResult = await runPnpmAudit();
    await checkOutdatedPackages();
    await checkUnusedDependencies();

    // Generate report
    const report = await generateSecurityReport();

    // Final summary
    log('\n📊 Summary', 'blue');
    log('==========', 'blue');

    if (auditResult.success && auditResult.vulnerabilities === 0) {
        log('✅ All security checks passed!', 'green');
        process.exit(0);
    } else if (auditResult.success) {
        log(`⚠️  Security audit completed with warnings`, 'yellow');
        log(`   Found ${auditResult.vulnerabilities} vulnerabilities below ${ACCEPTABLE_LEVEL} level`, 'yellow');
        process.exit(0);
    } else {
        log('❌ Security audit failed!', 'red');
        log('   Please fix critical vulnerabilities before proceeding', 'red');
        process.exit(1);
    }
}

// Run if called directly
if (require.main === module) {
    main().catch(error => {
        log('❌ Unexpected error during security audit', 'red');
        console.error(error);
        process.exit(1);
    });
}

module.exports = { runPnpmAudit, checkOutdatedPackages }; 